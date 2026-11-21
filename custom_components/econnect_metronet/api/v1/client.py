import copy
import logging
from contextlib import contextmanager
from functools import lru_cache
from threading import Lock

from requests import Session
from requests.exceptions import HTTPError

from . import query as q
from .decorators import require_lock, require_session
from .exceptions import (
    CodeError,
    CommandError,
    CredentialError,
    DeviceDisconnectedError,
    InvalidToken,
    LockError,
    ParseError,
    QueryNotValid,
)
from .router import Router
from .systems import (
    ELMO_E_CONNECT,
    ELMO_E_CONNECT_WEB_LOGIN,
    IESS_METRONET,
    IESS_METRONET_WEB_LOGIN,
)
from .utils import (
    _camel_to_snake_case,
    _sanitize_session_id,
    extract_session_id_from_html,
)

_LOGGER = logging.getLogger(__name__)


class ElmoClient:
    """ElmoClient class provides all the functionalities to connect to an Elmo system.

    During the authentication a short-lived token is stored
    in the instance and is used to arm/disarm the system.

    Usage:
        # Authenticate to the system (read-only mode)
        c = ElmoClient()
        c.auth("username", "password")

        # Obtain a lock to do actions on the system (write mode)
        with c.lock("alarm_code"):
            c.arm()     # Arms all alarms
            c.disarm()  # Disarm all alarms
    """

    def __init__(self, base_url=None, domain=None, session_id=None):
        self._router = Router(base_url)
        self._domain = domain
        self._session = Session()
        self._session_id = session_id
        self._panel = None
        self._lock = Lock()

        # Web login is required for E-Connect and Metronet because, at the moment, the
        # Cloud API login does not register the client session in their backend, causing
        # updates to be not received by the client during the long-polling `has_updates`.
        domain_url = "" if self._domain == "default" else self._domain
        self._web_login = base_url in [ELMO_E_CONNECT, IESS_METRONET]
        if base_url == ELMO_E_CONNECT:
            self._web_login_url = f"{ELMO_E_CONNECT_WEB_LOGIN}/{domain_url}"
        elif base_url == IESS_METRONET:
            self._web_login_url = f"{IESS_METRONET_WEB_LOGIN}/{domain_url}"
        else:
            self._web_login_url = None

        # Debug
        _LOGGER.debug(f"Client | Router: {self._router._base_url}")
        _LOGGER.debug(f"Client | Domain: {self._domain}")
        _LOGGER.debug(f"Client | Web login URL: {self._web_login_url}")

    def auth(self, username, password):
        """Authenticate the client and retrieves the access token.

        This method uses the Authentication API, or the web login form if the base_url is Elmo E-Connect.

        Args:
            username: the Username used for the authentication.
            password: the Password used for the authentication.

        Raises:
            HTTPError: if there is an error raised by the API (not 2xx response).
            CredentialError: if credentials are not correct
        Returns:
            The access token retrieved from the API. The token is also cached in
            the `ElmoClient` instance.
        """
        try:
            payload = {"username": username, "password": password}
            if self._domain is not None:
                payload["domain"] = self._domain

            _LOGGER.debug("Client | API Authentication")
            response = self._session.get(self._router.auth, params=payload)
            response.raise_for_status()
        except HTTPError as err:
            # 403: Incorrect username or password
            if err.response.status_code == 403:
                raise CredentialError from err
            raise

        # Store the session_id and the panel details (if available)
        data = response.json()
        self._session_id = data["SessionId"]
        self._panel = {_camel_to_snake_case(k): v for k, v in data.get("Panel", {}).items()}

        # Register the redirect URL and try the authentication again
        if data["Redirect"]:
            _LOGGER.debug(f"Redirect URL detected: {data['RedirectTo']}")
            self._router._base_url = data["RedirectTo"]
            redirect = self._session.get(self._router.auth, params=payload)
            redirect.raise_for_status()
            data = redirect.json()
            self._session_id = data["SessionId"]

        # Retrieve the session_id using the web login form
        if self._web_login:
            payload = {
                "IsDisableAccountCreation": "True",
                "IsAllowThemeChange": "True",
                "UserName": username,
                "Password": password,
                "RememberMe": "false",
            }
            web_response = self._session.post(self._web_login_url, data=payload)
            web_response.raise_for_status()
            self._session_id = extract_session_id_from_html(web_response.text)

        _LOGGER.debug(f"Client | Authentication successful: {_sanitize_session_id(self._session_id)}")
        return self._session_id

    @require_session
    def poll(self, ids):
        """Use a long-polling API to identify when something changes in the system.

        Calling this method blocks the thread for 15 seconds, waiting
        for a backend response that happens only when the alarm system status
        changes. Don't call this method from your main thread otherwise the
        application hangs.

        When the API returns that something is changed, you must call the
        `client.check()` to update your identifiers. Missing this step means
        that the next time you will call `client.poll()` the API returns immediately
        with an old result.

        Raises:
            HTTPError: if there is an error raised by the API (not 2xx response).
            ParseError: if the response cannot be parsed because the format is unexpected.

        Returns:
            A dictionary that includes what items have been changed. The following
            structure means that `areas` are not changed, while inputs are:
                {
                    "areas": False,
                    "inputs": True,
                    "outputs": False,
                    "statusAdv": False,
                }
        """
        payload = {
            "sessionId": self._session_id,
            "Areas": ids[q.SECTORS],
            "Inputs": ids[q.INPUTS],
            "Outputs": ids[q.OUTPUTS],
            "StatusAdv": ids[q.ALERTS],
            "CanElevate": "1",
            "ConnectionStatus": "1",
        }
        response = self._session.post(self._router.update, data=payload)
        response.raise_for_status()

        # Don't use state["HasChanges"] because it takes into account also events
        # that this client is ignoring. It forces the device to update too often.
        state = response.json()
        try:
            update = {
                "has_changes": state["Areas"] or state["Inputs"] or state["Outputs"] or state["StatusAdv"],
                "areas": state["Areas"],
                "inputs": state["Inputs"],
                "outputs": state["Outputs"],
                "statusadv": state["StatusAdv"],
            }
        except KeyError as err:
            raise ParseError(f"Client | Unable to parse poll response: {err} is missing") from err

        _LOGGER.debug(f"Client | Polling result: {update}")
        return update

    @contextmanager
    @require_session
    def lock(self, code, user_id=1):
        """Context manager to obtain a system lock.

        The alerting system allows only one user at a time and obtaining the lock is mandatory. When the
        context manager is closed, the lock is automatically released.

        Args:
            code: the alarm code used to obtain the lock.
            user_id: the `userId` used by some main units. This value is optional and
                should be used only if the main unit requires it. The default value is 1.

        Raises:
            CodeError: if used `code` is not valid.
            LockError: if the server is refusing to assign the lock. It could mean
            that an unexpected issue happened, or that another application is
            holding the lock. It's possible to retry the operation.
            HTTPError: if there is an error raised by the API (not 2xx response).

        Returns:
            A client instance with an acquired lock.
        """
        # Main units that do not require a userId param, expects userId to be "1"
        payload = {"userId": user_id, "password": code, "sessionId": self._session_id}
        response = self._session.post(self._router.lock, data=payload)
        _LOGGER.debug(f"Client | Lock response: {response.text}")

        try:
            response.raise_for_status()
        except HTTPError as err:
            # 403: Unable obtain the lock (race condition with another application)
            if err.response.status_code == 403:
                raise LockError from err
            # 401: The token has expired
            if err.response.status_code == 401:
                raise InvalidToken from err
            raise

        # A wrong code returns 200 with a fail state
        body = response.json()
        if not body[0]["Successful"]:
            raise CodeError

        self._lock.acquire()
        _LOGGER.debug("Client | Lock successful")
        try:
            yield self
        finally:
            self.unlock()

    @require_session
    @require_lock
    def unlock(self):
        """Release the system lock so that other threads (or this instance) can acquire the lock again.

        This method requires a valid session ID and if called
        when a Lock() is not acquired it bails out.

        If there is a server error or if the call fails, the lock is not released
        so the current thread can do further work before letting another thread
        gain the lock.

        Raises:
            HTTPError: if there is an error raised by the API (not 2xx response).

        Returns:
            A boolean if the lock has been released correctly.
        """
        payload = {"sessionId": self._session_id}
        response = self._session.post(self._router.unlock, data=payload)
        _LOGGER.debug(f"Client | Unlock response: {response.text}")
        response.raise_for_status()

        _LOGGER.debug("Client | Unlock successful")
        # Release the lock only in case of success, so that if it fails
        # the owner of the lock can properly unlock the system again
        # (maybe with a retry)
        self._lock.release()
        return True

    @require_session
    @require_lock
    def arm(self, sectors=None):
        """Arm system alarms without any activation delay.

        This API works only if a system lock has been obtained, otherwise the action ends with a failure.
        It is possible to enable ALL sectors, or provide a list of sectors such as:

            client.arm()        # Arms all sectors
            client.arm([3, 4])  # Arms only sectors 3 and 4

        Args:
            sector: (optional) list of sectors that must be armed. If the variable is
            empty, ALL is assumed and the entire system is armed. If multiple items
            are in the list, one request are sent to arm given sectors.

        Raises:
            HTTPError: if there is an error raised by the API (not 2xx response).

        Returns:
            A boolean if the system has been armed correctly.
        """
        sectors = sectors or []

        if sectors:
            # Arm only selected sectors
            _LOGGER.debug(f"Client | Arming sectors: {sectors}")
            payload = {
                "CommandType": 1,
                "ElementsClass": 9,
                "ElementsIndexes": sectors,
                "sessionId": self._session_id,
            }
        else:
            # Arm ALL sectors
            _LOGGER.debug("Client | Arming all sectors")
            payload = {
                "CommandType": 1,
                "ElementsClass": 1,
                "ElementsIndexes": 1,
                "sessionId": self._session_id,
            }

        # Send the payload to arm sectors
        response = self._session.post(self._router.send_command, data=payload)
        _LOGGER.debug(f"Client | Arm response: {response.text}")
        response.raise_for_status()
        body = response.json()

        # Errors returns 200 with "Successful == False" JSON key
        if not body[0]["Successful"]:
            raise CommandError

        _LOGGER.debug("Client | Arm successful")
        return True

    @require_session
    @require_lock
    def disarm(self, sectors=None):
        """Disarm system alarms.

        This API works only if a system lock has been obtained, otherwise the action ends with a failure.
        It is possible to disable ALL sectors, or provide a list of sectors such as:

            client.disarm()     # Disarms all sectors
            client.disarm([3])  # Disarms only sector 3

        Args:
            sector: (optional) list of sectors that must be disarmed. If the variable is
            empty, ALL is assumed and the entire system is disarmed. If multiple items
            are in the list, multiple requests are sent to disarm given sectors.

        Raises:
            HTTPError: if there is an error raised by the API (not 2xx response).

        Returns:
            A boolean if the system has been disarmed correctly.
        """
        sectors = sectors or []

        if sectors:
            # Disarm only selected sectors
            _LOGGER.debug(f"Client | Disarming sectors: {sectors}")
            payload = {
                "CommandType": 2,
                "ElementsClass": 9,
                "ElementsIndexes": sectors,
                "sessionId": self._session_id,
            }

        else:
            # Disarm ALL sectors
            _LOGGER.debug("Client | Disarming all sectors")
            payload = {
                "CommandType": 2,
                "ElementsClass": 1,
                "ElementsIndexes": 1,
                "sessionId": self._session_id,
            }

        # Send the payload to disarm sectors
        response = self._session.post(self._router.send_command, data=payload)
        _LOGGER.debug(f"Client | Disarm response: {response.text}")
        response.raise_for_status()
        body = response.json()

        # Errors returns 200 with "Successful == False" JSON key
        if not body[0]["Successful"]:
            raise CommandError

        _LOGGER.debug("Client | Disarm successful")
        return True

    @require_session
    @require_lock
    def exclude(self, inputs):
        """Exclude passed inputs: they are not alarmed when you arm the area they belongs to.

        This API provides the same effects as turning them
        from "idle" to "bypassed" on the E-Connect web UI.

        This API works only if a system lock has been
        obtained, otherwise the action ends with a failure.
        It is possible to provide a list of inputs such as:

            client.exclude([3])  # Excludes only input 3
            client.exclude([3, 5])  # Excludes input 3 and 5

        Args:
            inputs: list of inputs that must be excluded. If multiple items
            are in the list, multiple requests are sent to exclude given inputs.

        Raises:
            HTTPError: if there is an error raised by the API (not 2xx response).

        Returns:
            A boolean if the input has been excluded correctly.
        """
        payloads = []

        # Exclude only selected inputs
        _LOGGER.debug(f"Client | Excluding inputs: {inputs}")
        for element in inputs:
            payloads.append(
                {
                    "CommandType": 2,
                    "ElementsClass": 10,
                    "ElementsIndexes": element,
                    "sessionId": self._session_id,
                }
            )

        # Excluding multiple inputs requires multiple requests
        errors = []
        for payload in payloads:
            response = self._session.post(self._router.send_command, data=payload)
            response.raise_for_status()

            # A not existing input returns 200 with a fail state
            body = response.json()
            _LOGGER.debug(f"Client | Excluding response: {body}")
            if not body[0]["Successful"]:
                errors.append(payload["ElementsIndexes"])

        # Raise an exception if errors are detected
        if errors:
            invalid_inputs = ",".join(str(x) for x in errors)
            raise CommandError(f"Selected inputs don't exist: {invalid_inputs}")

        _LOGGER.debug("Client | Excluding successful")
        return True

    @require_session
    @require_lock
    def include(self, inputs):
        """Include system inputs: they are alarmed when you arm the area they belongs to.

        This API provides the same effects as turning them
        from "bypassed" to "idle" on the E-Connect web UI.

        This API works only if a system lock has been
        obtained, otherwise the action ends with a failure.
        It is possible to provide a list of inputs such as:

            client.include([3])  # Includes only input 3
            client.include([3, 5])  # Includes input 3 and 5

        Args:
            inputs: list of inputs that must be included. If multiple items
            are in the list, multiple requests are sent to include given inputs.

        Raises:
            HTTPError: if there is an error raised by the API (not 2xx response).

        Returns:
            A boolean if the input has been included correctly.
        """
        payloads = []

        # Include only selected inputs
        _LOGGER.debug(f"Client | Including inputs: {inputs}")
        for element in inputs:
            payloads.append(
                {
                    "CommandType": 1,
                    "ElementsClass": 10,
                    "ElementsIndexes": element,
                    "sessionId": self._session_id,
                }
            )

        # Including multiple inputs requires multiple requests
        errors = []
        for payload in payloads:
            response = self._session.post(self._router.send_command, data=payload)
            response.raise_for_status()

            # A not existing input returns 200 with a fail state
            body = response.json()
            _LOGGER.debug(f"Client | Including response: {body}")
            if not body[0]["Successful"]:
                errors.append(payload["ElementsIndexes"])

        # Raise an exception if errors are detected
        if errors:
            invalid_inputs = ",".join(str(x) for x in errors)
            raise CommandError(f"Selected inputs don't exist: {invalid_inputs}")

        _LOGGER.debug("Client | Including successful")
        return True

    @require_session
    def turn_on(self, outputs):
        """Turn on passed outputs.

        This API provides the same effects as turning them
        from "not active" to "active" on the E-Connect web UI.

        Only outputs that are configured in the control panel with the option
        "Manual Control" can be turned on
        If the output is configured with "Require Authentication" flag in the control panel
        can be turned on only if the panel is locked

            client.turn_on([3])  # Turn on only output 3
            client.turn_on([3, 5])  # Turn on output 3 and 5

        Args:
            outputs: list of outputs that must be turned on. If multiple items
            are in the list, one requests is sent to turn on given outputs.

        Raises:
            HTTPError: if there is an error raised by the API (not 2xx response).

        Returns:
            A boolean if the output has been turned on correctly.
        """
        # Exclude only selected inputs
        _LOGGER.debug(f"Client | Turning on outputs: {outputs}")
        payload = {
            "CommandType": 1,
            "ElementsClass": 12,
            "ElementsIndexes": outputs,
            "sessionId": self._session_id,
        }

        # Send turn on request
        response = self._session.post(self._router.send_command, data=payload)
        response.raise_for_status()
        body = response.json()

        # Errors returns 200 with "Successful == False" JSON key
        if not body[0]["Successful"]:
            _LOGGER.error(f"Client | Turning on response: {body}")
            raise CommandError

        _LOGGER.debug(f"Client | Turning on successful with response: {body}")
        return True

    @require_session
    def turn_off(self, outputs):
        """Turn off passed outputs.

        This API provides the same effects as turning them
        from "active" to "not active" on the E-Connect web UI.

        Only outputs that are configured in the control panel with the option
        "Manual Control" can be turned off
        If the output is configured with "Require Authentication" flag in the control panel
        can be turned off only if the panel is locked

            client.turn_off([3])  # Turn off only output 3
            client.turn_off([3, 5])  # Turn off output 3 and 5

        Args:
            outputs: list of outputs that must be turned off. If multiple items
            are in the list, one requests is sent to turn off given outputs.

        Raises:
            HTTPError: if there is an error raised by the API (not 2xx response).

        Returns:
            A boolean if the output has been turned off correctly.
        """
        # Turn off only selected outputs
        _LOGGER.debug(f"Client | Turning off outputs: {outputs}")
        payload = {
            "CommandType": 2,
            "ElementsClass": 12,
            "ElementsIndexes": outputs,
            "sessionId": self._session_id,
        }

        # Send turn off request
        response = self._session.post(self._router.send_command, data=payload)
        response.raise_for_status()
        body = response.json()

        # Errors returns 200 with "Successful == False" JSON key
        if not body[0]["Successful"]:
            _LOGGER.error(f"Client | Turning on response: {body}")
            raise CommandError

        _LOGGER.debug(f"Client | Turning on successful with response: {body}")
        return True

    @lru_cache(maxsize=1)
    @require_session
    def _get_descriptions(self):
        """Retrieve Sectors and Inputs names to map `Class` and `Index` into a human readable description.

        This method calls the E-Connect API, but the
        result is cached for the entire `ElmoClient` life-cycle.

        Raises:
            HTTPError: if there is an error raised by the API (not 2xx response).

        Returns:
            A dictionary having `Class` as key, and a dictionary of strings (`Index`)
            as a value, to map sectors and inputs names.
        """
        payload = {"sessionId": self._session_id}
        response = self._session.post(self._router.descriptions, data=payload)
        response.raise_for_status()

        # Transform the list of items in a dict -> dict of strings
        descriptions = {}
        items = response.json()
        _LOGGER.debug(f"Client | Descriptions response: {items}")
        for item in items:
            classes = descriptions.get(item["Class"], {})
            classes[item["Index"]] = item["Description"]
            descriptions[item["Class"]] = classes

        _LOGGER.debug(f"Client | Descriptions retrieved (in-cache): {descriptions}")
        return descriptions

    @require_session
    def query(self, query):
        """Query an Elmo System to retrieve registered entries.

        It's possible to query different part of the system using the
        `custom_components.econnect_metronet.api.v1.query` module:

            from custom_components.econnect_metronet.api.v1 import query

            sectors = client.query(query.SECTORS).get("sectors")
            inputs = client.query(query.INPUTS).get("inputs")
            outputs = client.query(query.OUTPUTS).get("outputs")

        Raises:
            QueryNotValid: if the query is not recognized.
            HTTPError: if there is an error raised by the API (not 2xx response).
            ParseError: if the response cannot be parsed because the format is unexpected.

        Returns:
            A dict representing the raw query retrieved by the backend call.

            `last_id`: is the last ID of the query, used to retrieve new state changes
            `sectors`: is the key you use to retrieve sectors if that was the query
            `inputs`: is the key you use to retrieve inputs if that was the query
            'outputs`: is the key you use to retrieve outputs if that was the query
        """
        # Query detection
        if query == q.SECTORS:
            key_group = "sectors"
            endpoint = self._router.sectors
            _LOGGER.debug("Client | Querying sectors")
        elif query == q.INPUTS:
            key_group = "inputs"
            endpoint = self._router.inputs
            _LOGGER.debug("Client | Querying inputs")
        elif query == q.OUTPUTS:
            key_group = "outputs"
            endpoint = self._router.outputs
            _LOGGER.debug("Client | Querying outputs")
        elif query == q.ALERTS:
            endpoint = self._router.status
            _LOGGER.debug("Client | Querying alerts")
        elif query == q.PANEL:
            _LOGGER.debug("Client | Querying panel details (cached)")
            return {
                "last_id": 0,
                "panel": copy.deepcopy(self._panel) if self._panel else {},
            }
        else:
            # Bail-out if the query is not recognized
            raise QueryNotValid()

        try:
            response = self._session.post(endpoint, data={"sessionId": self._session_id})
            response.raise_for_status()
        except HTTPError as err:
            # Handle the case when the device is disconnected
            if err.response.status_code == 403 and "Centrale non connessa" in err.response.text:
                raise DeviceDisconnectedError from err
            raise

        if query in [q.SECTORS, q.INPUTS, q.OUTPUTS]:
            # Retrieve description or use the cache
            descriptions = self._get_descriptions()

            # Filter only entries that are used
            # `excluded` field is available only on inputs, but to return the same `dict`
            # structure, we default "excluded" as False for sectors. In fact, sectors
            # are never excluded.
            entries = response.json()
            _LOGGER.debug(f"Client | Query response: {entries}")
            items = {}

            try:
                # Determine the last_id by finding the maximum Id in the list
                last_id = max(entry["Id"] for entry in entries)
            except (TypeError, ValueError) as err:
                _LOGGER.error("Client | Could not determine max Id from entries, defaulting to 0.")
                _LOGGER.debug(f"Client | Error: {err} | Entries: {entries}")
                last_id = 0

            result = {
                "last_id": last_id,
                key_group: items,
            }
            try:
                for entry in entries:
                    if entry["InUse"]:
                        # Address potential data inconsistency between cloud data and main unit.
                        # In some installations, they may be out of sync, resulting in the cloud
                        # providing a sector/input/output that doesn't actually exist in the main unit.
                        # This case happens also when all inputs or sectors or outputs are used in the
                        # main unit, but their strings are not synchronized with the cloud.
                        # To handle this, we default the name to "Unknown" if its description
                        # isn't found in the cloud data to prevent KeyError.
                        description = descriptions.get(query, {})
                        item = {
                            "id": entry.get("Id"),
                            "index": entry.get("Index"),
                            "element": entry.get("Element"),
                            "name": description.get(entry["Index"], "Unknown"),
                        }

                        if query == q.SECTORS:
                            item.update(
                                {
                                    "activable": entry.get("Activable", False),
                                    "status": entry.get("Active", False),
                                }
                            )
                            _LOGGER.debug("Client | Querying sectors")
                        elif query == q.INPUTS:
                            item.update(
                                {
                                    "excluded": entry.get("Excluded", False),
                                    "status": entry.get("Alarm", False),
                                }
                            )
                            _LOGGER.debug("Client | Querying inputs")
                        elif query == q.OUTPUTS:
                            item.update(
                                {
                                    "do_not_require_authentication": entry.get("DoNotRequireAuthentication", False),
                                    "control_denied_to_users": entry.get("ControlDeniedToUsers", False),
                                    "status": entry.get("Active", False),
                                }
                            )
                            _LOGGER.debug("Client | Querying outputs")

                        items[entry.get("Index")] = item
            except KeyError as err:
                raise ParseError(f"Client | Unable to parse query response: {err}") from err

            _LOGGER.debug(f"Client | Query parsed successfully: {result}")
            return result
        elif query == q.ALERTS:
            try:
                # Check if the response has the expected format
                msg = response.json()
                last_id = msg["StatusUid"]
                status = msg["PanelLeds"]
                anomalies = msg["PanelAnomalies"]
            except (KeyError, ValueError) as err:
                raise ParseError("Unexpected response format from the server.") from err

            # Merge the 'status' and 'anomalies' dictionaries
            merged_dict = {**status, **anomalies}

            # Convert the dict to a snake_case one to simplify the usage in other modules, and sort alphabetically
            new_dict = {
                "last_id": last_id,
                "alerts": {
                    i: {"name": _camel_to_snake_case(k), "status": v}
                    for i, (k, v) in enumerate(sorted(merged_dict.items()))
                },
            }
            _LOGGER.debug(f"Client | Status retrieved: {new_dict}")

            return new_dict
        else:
            raise QueryNotValid()  # pragma: no cover
