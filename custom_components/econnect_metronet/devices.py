import logging
from typing import Union

from elmo import query as q
from elmo.api.exceptions import (
    CodeError,
    CommandError,
    CredentialError,
    DeviceDisconnectedError,
    LockError,
    ParseError,
)
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from requests.exceptions import HTTPError

from .const import (
    CONF_AREAS_ARM_AWAY,
    CONF_AREAS_ARM_HOME,
    CONF_AREAS_ARM_NIGHT,
    CONF_AREAS_ARM_VACATION,
    CONF_MANAGE_SECTORS,
    NOTIFICATION_MESSAGE,
)
from .helpers import split_code

_LOGGER = logging.getLogger(__name__)


class AlarmDevice:
    """AlarmDevice class represents an e-connect alarm system. This method wraps around
    a connector object (e.g. `ElmoClient`) so that the client can be stateless and just
    return data, while this class persists the status of the alarm.

    Usage:
        # Initialization
        conn = ElmoClient()
        device = AlarmDevice(conn)

        # Connect automatically grab the latest status
        device.connect("username", "password")
        print(device.state)
    """

    def __init__(self, connection, config=None):
        # Configuration and internals
        self.connected = False
        self._inventory = {}
        self._sectors = {}
        self._connection = connection
        self._last_ids = {
            q.SECTORS: 0,
            q.INPUTS: 0,
            q.OUTPUTS: 0,
            q.ALERTS: 0,
        }

        # Load user configuration
        config = config or {}
        self._managed_sectors = config.get(CONF_MANAGE_SECTORS) or []
        self._sectors_away = config.get(CONF_AREAS_ARM_AWAY) or []
        self._sectors_home = config.get(CONF_AREAS_ARM_HOME) or []
        self._sectors_night = config.get(CONF_AREAS_ARM_NIGHT) or []
        self._sectors_vacation = config.get(CONF_AREAS_ARM_VACATION) or []

        # Alarm state
        self.state = None

    def _register_sector(self, entity):
        """Register a sector entity in the device's internal inventory."""
        entity_id = entity.entity_id.split(".")[1]
        self._sectors[entity_id] = self._inventory[q.SECTORS][entity._sector_id]["element"]

    @property
    def panel(self):
        """Return the panel status."""
        return self._inventory.get(q.PANEL, {})

    @property
    def inputs(self):
        """Iterate over the device's inventory of inputs.
        This property provides an iterator over the device's inventory, where each item is a tuple
        containing the input's ID and its name.
        Yields:
            tuple: A tuple where the first item is the input ID and the second item is the input name.
        Example:
            >>> device = AlarmDevice()
            >>> list(device.inputs)
            [(1, 'Front Door'), (2, 'Back Door')]
        """
        for input_id, item in self._inventory.get(q.INPUTS, {}).items():
            yield input_id, item["name"]

    @property
    def outputs(self):
        """Iterate over the device's inventory of outputs.
        This property provides an iterator over the device's inventory, where each item is a tuple
        containing the output's ID and its name.
        Yields:
            tuple: A tuple where the first item is the output ID and the second item is the output name.
        Example:
            >>> device = AlarmDevice()
            >>> list(device.outputs)
            [(1, 'Output 1'), (2, 'Output 2')]
        """
        for input_id, item in self._inventory.get(q.OUTPUTS, {}).items():
            yield input_id, item["name"]

    @property
    def sectors(self):
        """Iterate over the device's inventory of sectors.
        This property provides an iterator over the device's inventory, where each item is a tuple
        containing the sectors's ID and its name.
        Yields:
            tuple: A tuple where the first item is the sector ID and the second item is the sector name.
        Example:
            >>> device = AlarmDevice()
            >>> list(device.sectors)
            [(1, 'S1 Living Room'), (2, 'S2 Bedroom')]
        """
        for sector_id, item in self._inventory.get(q.SECTORS, {}).items():
            yield sector_id, item["name"]

    @property
    def alerts(self):
        """Iterate over the device's inventory of alerts.
        This property provides an iterator over the device's inventory, where each item is a tuple
        containing the alerts's ID and its name.
        Yields:
            tuple: A tuple where the first item is the alert ID and the second item is the alert name.
        Example:
            >>> device = AlarmDevice()
            >>> list(device.alerts)
            [{1: "alarm_led", 2: "anomalies_led"}]
        """
        for alert_id, item in self._inventory.get(q.ALERTS, {}).items():
            yield alert_id, item["name"]

    def items(self, query, status=None):
        """Iterate over items from the device's inventory based on a query and optional status filter.
        This method provides an iterator over the items in the device's inventory that match the given query.
        If a status is provided, only items with that status will be yielded.
        Args:
            query (str): The query string to match against items in the inventory.
            status (Optional[Any]): An optional status filter. If provided, only items with this status
                                    will be yielded. Defaults to None, which means all items matching the query
                                    will be yielded regardless of their status.
        Yields:
            tuple: A tuple where the first item is the item ID and the second item is the item dictionary.
        Example:
            >>> device = AlarmDevice()
            >>> list(device.items('door', status=True))
            [(1, {'name': 'Front Door', 'status': True, ...})]
        """
        for item_id, item in self._inventory.get(query, {}).items():
            if status is None or item.get("status") == status:
                yield item_id, item

    def connect(self, username, password):
        """Establish a connection with the E-connect backend, to retrieve an access
        token. This method stores the `session_id` within the `ElmoClient` object
        and is used automatically when other methods are called.

        When a connection is successfully established, the device automatically
        updates the status calling `self.update()`.
        """
        try:
            self._connection.auth(username, password)
            self.connected = True
        except HTTPError as err:
            _LOGGER.error(f"Device | Error while authenticating with e-Connect: {err}")
            raise err
        except CredentialError as err:
            _LOGGER.error(f"Device | Username or password are not correct: {err}")
            raise err

    def has_updates(self):
        """Check if there have been any updates using the established connection.

        This method uses the connection to detect possible changes. It's a blocking
        call that requests for the system unit status to detect possible connection issues,
        and then polls for updates. The method blocks for 15 seconds and it should not be
        invoked from the main thread.

        Raises:
            HTTPError: If there's an error while polling for updates.
            ParseError: If there's an error parsing the poll response.

        Returns:
            dict: Dictionary with the updates if any, based on the last known IDs.
        """
        try:
            self._connection.query(q.ALERTS)
            data = self._connection.poll({key: value for key, value in self._last_ids.items()})
            self.connected = True
            return data
        except HTTPError as err:
            _LOGGER.error(f"Device | Error while polling for updates: {err.response.text}")
            raise err
        except ParseError as err:
            _LOGGER.error(f"Device | Error parsing the poll response: {err}")
            raise err
        except DeviceDisconnectedError as err:
            self.connected = False
            raise err

    def get_state(self):
        """Determine the alarm state based on the armed sectors.

        This method evaluates the armed sectors and maps them to predefined
        alarm states: home, night, or away. If no sectors are armed, it returns
        a disarmed state. For accurate comparisons, the method sorts the sectors
        internally, ensuring robustness against potentially unsorted input.

        Returns:
            str: One of the predefined HA alarm states.
        """
        # If the system is arming or disarming, return the current state
        # to prevent the state from being updated while the system is in transition.
        if self.state in [AlarmControlPanelState.ARMING, AlarmControlPanelState.DISARMING]:
            return self.state

        sectors_armed = dict(self.items(q.SECTORS, status=True))
        if not sectors_armed:
            return AlarmControlPanelState.DISARMED

        # Note: `element` is the sector ID you use to arm/disarm the sector.
        sectors = [sectors["element"] for sectors in sectors_armed.values()]
        # Sort lists here for robustness, ensuring accurate comparisons
        # regardless of whether the input lists were pre-sorted or not.
        sectors_armed_sorted = sorted(sectors)
        if sectors_armed_sorted == sorted(self._sectors_home):
            return AlarmControlPanelState.ARMED_HOME

        if sectors_armed_sorted == sorted(self._sectors_night):
            return AlarmControlPanelState.ARMED_NIGHT

        if sectors_armed_sorted == sorted(self._sectors_vacation):
            return AlarmControlPanelState.ARMED_VACATION

        return AlarmControlPanelState.ARMED_AWAY

    def get_status(self, query: int, id: int) -> Union[bool, int]:
        """Get the status of an item in the device inventory specified by query and id.

        Parameters:
            query (int): The query index.
            id (int): The item ID.

        Returns:
            int: The status of the item.
        """
        if query == q.ALERTS and id == -1:
            # Connection Status Alert
            # NOTE: we should turn on the sensor (alert) if the device is not connected, hence the `not`
            return not self.connected

        return self._inventory[query][id]["status"]

    def update(self):
        """Updates the internal state of the device based on the latest data.

        This method performs the following actions:
        1. Queries for the latest sectors and inputs using the internal connection.
        2. Filters the retrieved sectors and inputs to categorize them based on their status.
        3. Updates the last known IDs for sectors and inputs.
        4. Updates internal state for sectors' and inputs' statuses.

        Returns:
            dict: A dictionary containing the latest retrieved inventory.

        Raises:
            HTTPError: If there's an error while making the HTTP request.
            ParseError: If there's an error while parsing the response.

        Attributes updated:
            _last_ids (dict): Updated last known IDs for sectors and inputs.
            state (str): Updated internal state of the device.
        """
        # Retrieve sectors and inputs
        try:
            sectors = self._connection.query(q.SECTORS)
            inputs = self._connection.query(q.INPUTS)
            outputs = self._connection.query(q.OUTPUTS)
            alerts = self._connection.query(q.ALERTS)
            panel = self._connection.query(q.PANEL)
        except HTTPError as err:
            _LOGGER.error(f"Device | Error during the update: {err.response.text}")
            raise err
        except ParseError as err:
            _LOGGER.error(f"Device | Error during the update: {err}")
            raise err
        except DeviceDisconnectedError as err:
            self.connected = False
            raise err

        # `last_id` equal to 1 means the connection has been reset and the update
        # is an empty state. See: https://github.com/palazzem/ha-econnect-alarm/issues/148
        if sectors.get("last_id") == 1:
            _LOGGER.debug("Device | The connection has been reset, skipping the update")
            return self._inventory

        # Update the _inventory
        self.connected = True
        self._inventory.update({q.SECTORS: sectors["sectors"]})
        self._inventory.update({q.INPUTS: inputs["inputs"]})
        self._inventory.update({q.OUTPUTS: outputs["outputs"]})
        self._inventory.update({q.ALERTS: alerts["alerts"]})
        self._inventory.update({q.PANEL: panel["panel"]})

        # Update the _last_ids
        self._last_ids[q.SECTORS] = sectors.get("last_id", 0)
        self._last_ids[q.INPUTS] = inputs.get("last_id", 0)
        self._last_ids[q.OUTPUTS] = outputs.get("last_id", 0)
        self._last_ids[q.ALERTS] = alerts.get("last_id", 0)
        self._last_ids[q.PANEL] = panel.get("last_id", 0)

        # Filter out the sectors that are not managed
        # NOTE: this change is internal and not exposed to users as the feature is experimental. Further
        # development requires that users can register multiple devices and alarm panels to control
        # sectors in a more granular way. See: https://github.com/palazzem/ha-econnect-alarm/issues/95
        if self._managed_sectors:
            self._inventory[q.SECTORS] = {
                k: v for k, v in self._inventory[q.SECTORS].items() if v["element"] in self._managed_sectors
            }

        # Update the internal state machine (mapping state)
        self.state = self.get_state()

        return self._inventory

    def arm(self, code, sectors=None):
        try:
            # Detect if the user is trying to arm a system that requires a user ID
            if not self.panel.get("login_without_user_id", True):
                user_id, code = split_code(code)
            else:
                user_id = 1

            with self._connection.lock(code, user_id=user_id):
                self._connection.arm(sectors=sectors)
        except HTTPError as err:
            _LOGGER.error(f"Device | Error while arming the system: {err.response.text}")
            raise err
        except LockError as err:
            _LOGGER.error(f"Device | Error while acquiring the system lock: {err}")
            raise err
        except CodeError as err:
            _LOGGER.error(f"Device | Credentials (alarm code) is incorrect: {err}")
            raise err
        except CommandError as err:
            _LOGGER.error(f"Device | Error while arming the system: {err}")
            raise err

    def disarm(self, code, sectors=None):
        try:
            # Detect if the user is trying to arm a system that requires a user ID
            if not self.panel.get("login_without_user_id", True):
                user_id, code = split_code(code)
            else:
                user_id = 1

            # Detect which sectors should be disarmed
            if sectors is None:
                sectors = [sector["element"] for _, sector in self.items(q.SECTORS, status=True)]

            with self._connection.lock(code, user_id=user_id):
                self._connection.disarm(sectors=sectors)
        except HTTPError as err:
            _LOGGER.error(f"Device | Error while disarming the system: {err.response.text}")
            raise err
        except LockError as err:
            _LOGGER.error(f"Device | Error while acquiring the system lock: {err}")
            raise err
        except CodeError as err:
            _LOGGER.error(f"Device | Credentials (alarm code) is incorrect: {err}")
            raise err
        except CommandError as err:
            _LOGGER.error(f"Device | Error while disarming the system: {err}")
            raise err

    def turn_off(self, output):
        """
        Turn off a specified output.

        Args:
            output: The ID of the output to be turned off.

        Raises:
            HTTPError: If there is an error in the HTTP request to turn off the output.

        Notes:
            - The `element` is the sector ID used to arm/disarm the sector.
            - This method checks for authentication requirements and control permissions
                before attempting to turn off the output.
            - If the output can't be manually controlled or if authentication is required but not provided,
                appropriate error messages are logged.

        Example:
            To turn off an output with ID '1', use:
            >>> device_instance.turn_off(1)
        """
        for id, item in self.items(q.OUTPUTS):
            # Skip if it's not matching the output
            if id != output:
                continue

            # If the output isn't manual controllable by users write an error il log
            if item.get("control_denied_to_users"):
                _LOGGER.warning(
                    f"Device | Error while turning off output: {item.get('name')}, Can't be manual controlled"
                )
                _LOGGER.warning(NOTIFICATION_MESSAGE)
                break

            # If the output require authentication for control write an error il log
            if not item.get("do_not_require_authentication"):
                _LOGGER.warning(f"Device | Error while turning off output: {item.get('name')}, Required authentication")
                _LOGGER.warning(NOTIFICATION_MESSAGE)
                break

            try:
                element_id = item.get("element")
                self._connection.turn_off(element_id)
                return True
            except HTTPError as err:
                _LOGGER.error(f"Device | Error while turning off output: {err.response.text}")
                raise err
            except CommandError as err:
                _LOGGER.error(f"Device | Error while turning off output: {err}")
                raise err
        return False

    def turn_on(self, output):
        """
        Turn on a specified output.

        Args:
            output: The ID of the output to be turned on.

        Raises:
            HTTPError: If there is an error in the HTTP request to turn on the output.

        Notes:
            - The `element` is the sector ID used to arm/disarm the sector.
            - This method checks for authentication requirements and control permissions
                before attempting to turn on the output.
            - If the output can't be manually controlled or if authentication is required but not provided,
                appropriate error messages are logged.

        Example:
            To turn on an output with ID '1', use:
            >>> device_instance.turn_on(1)
        """
        for id, item in self.items(q.OUTPUTS):
            # Skip if it's not matching the output
            if id != output:
                continue

            # If the output isn't manual controllable by users write an error log
            if item.get("control_denied_to_users"):
                _LOGGER.warning(
                    f"Device | Error while turning on output: {item.get('name')}, Can't be manual controlled"
                )
                _LOGGER.warning(NOTIFICATION_MESSAGE)
                break

            # If the output require authentication for control write an error log
            if not item.get("do_not_require_authentication"):
                _LOGGER.warning(f"Device | Error while turning on output: {item.get('name')}, Required authentication")
                _LOGGER.warning(NOTIFICATION_MESSAGE)
                break

            try:
                element_id = item.get("element")
                self._connection.turn_on(element_id)
                return True
            except HTTPError as err:
                _LOGGER.error(f"Device | Error while turning on outputs: {err.response.text}")
                raise err
            except CommandError as err:
                _LOGGER.error(f"Device | Error while turning on outputs: {err}")
                raise err
        return False
