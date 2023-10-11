import logging

from elmo import query as q
from elmo.api.exceptions import CodeError, CredentialError, LockError, ParseError
from elmo.utils import _filter_data
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMED_VACATION,
    STATE_ALARM_DISARMED,
    STATE_UNAVAILABLE,
)
from requests.exceptions import HTTPError

from .const import CONF_AREAS_ARM_HOME, CONF_AREAS_ARM_NIGHT, CONF_AREAS_ARM_VACATION
from .helpers import parse_areas_config

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
        self._connection = connection
        self._sectors_home = []
        self._sectors_night = []
        self._sectors_vacation = []
        self._lastIds = {
            q.SECTORS: 0,
            q.INPUTS: 0,
        }

        # Load user configuration
        if config is not None:
            self._sectors_home = parse_areas_config(config.get(CONF_AREAS_ARM_HOME))
            self._sectors_night = parse_areas_config(config.get(CONF_AREAS_ARM_NIGHT))
            self._sectors_vacation = parse_areas_config(config.get(CONF_AREAS_ARM_VACATION))

        # Alarm state
        self.state = STATE_UNAVAILABLE
        self.alerts = {}
        self.sectors_armed = {}
        self.sectors_disarmed = {}
        self.inputs_alerted = {}
        self.inputs_wait = {}
        self._inventory = {}

    @property
    def inputs(self):
        for input_id, item in self._inventory.get("inputs", {}).items():
            yield input_id, item["name"]

    @property
    def sectors(self):
        for sector_id, item in self._inventory.get("sectors", {}).items():
            yield sector_id, item["name"]

    @property
    def alerts_v2(self):
        yield from self._inventory.get("alerts", {}).items()

    def connect(self, username, password):
        """Establish a connection with the E-connect backend, to retrieve an access
        token. This method stores the `session_id` within the `ElmoClient` object
        and is used automatically when other methods are called.

        When a connection is successfully established, the device automatically
        updates the status calling `self.update()`.
        """
        try:
            self._connection.auth(username, password)
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
            self._connection.get_status()
            return self._connection.poll({key: value for key, value in self._lastIds.items()})
        except HTTPError as err:
            _LOGGER.error(f"Device | Error while polling for updates: {err.response.text}")
            raise err
        except ParseError as err:
            _LOGGER.error(f"Device | Error parsing the poll response: {err}")
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
        if not self.sectors_armed:
            return STATE_ALARM_DISARMED

        # Note: `element` is the sector ID you use to arm/disarm the sector.
        sectors = [sectors["element"] for sectors in self.sectors_armed.values()]
        # Sort lists here for robustness, ensuring accurate comparisons
        # regardless of whether the input lists were pre-sorted or not.
        sectors_armed_sorted = sorted(sectors)
        if sectors_armed_sorted == sorted(self._sectors_home):
            return STATE_ALARM_ARMED_HOME

        if sectors_armed_sorted == sorted(self._sectors_night):
            return STATE_ALARM_ARMED_NIGHT

        if sectors_armed_sorted == sorted(self._sectors_vacation):
            return STATE_ALARM_ARMED_VACATION

        return STATE_ALARM_ARMED_AWAY

    def update(self):
        """Updates the internal state of the device based on the latest data.

        This method performs the following actions:
        1. Queries for the latest sectors and inputs using the internal connection.
        2. Filters the retrieved sectors and inputs to categorize them based on their status.
        3. Updates the last known IDs for sectors and inputs.
        4. Updates internal state for sectors' and inputs' statuses.

        Raises:
            HTTPError: If there's an error while making the HTTP request.
            ParseError: If there's an error while parsing the response.

        Attributes updated:
            sectors_armed (dict): A dictionary of sectors that are armed.
            sectors_disarmed (dict): A dictionary of sectors that are disarmed.
            inputs_alerted (dict): A dictionary of inputs that are in an alerted state.
            inputs_wait (dict): A dictionary of inputs that are in a wait state.
            _lastIds (dict): Updated last known IDs for sectors and inputs.
            state (str): Updated internal state of the device.
        """
        # Retrieve sectors and inputs
        try:
            sectors = self._connection.query(q.SECTORS)
            inputs = self._connection.query(q.INPUTS)
            alerts = self._connection.get_status()
        except HTTPError as err:
            _LOGGER.error(f"Device | Error during the update: {err.response.text}")
            raise err
        except ParseError as err:
            _LOGGER.error(f"Device | Error during the update: {err}")
            raise err

        # Update the _inventory
        self._inventory.update({"inputs": inputs["inputs"]})
        self._inventory.update({"sectors": sectors["sectors"]})
        self._inventory.update({"alerts": alerts})

        # Filter sectors and inputs
        self.sectors_armed = _filter_data(sectors, "sectors", True)
        self.sectors_disarmed = _filter_data(sectors, "sectors", False)
        self.inputs_alerted = _filter_data(inputs, "inputs", True)
        self.inputs_wait = _filter_data(inputs, "inputs", False)

        self._lastIds[q.SECTORS] = sectors.get("last_id", 0)
        self._lastIds[q.INPUTS] = inputs.get("last_id", 0)

        # Update system alerts
        self.alerts = alerts

        # Update the internal state machine (mapping state)
        self.state = self.get_state()

        return self._inventory

    def arm(self, code, sectors=None):
        try:
            with self._connection.lock(code):
                self._connection.arm(sectors=sectors)
                self.state = STATE_ALARM_ARMED_AWAY
        except HTTPError as err:
            _LOGGER.error(f"Device | Error while arming the system: {err.response.text}")
            raise err
        except LockError as err:
            _LOGGER.error(f"Device | Error while acquiring the system lock: {err}")
            raise err
        except CodeError as err:
            _LOGGER.error(f"Device | Credentials (alarm code) is incorrect: {err}")
            raise err

    def disarm(self, code, sectors=None):
        try:
            with self._connection.lock(code):
                self._connection.disarm(sectors=sectors)
                self.state = STATE_ALARM_DISARMED
        except HTTPError as err:
            _LOGGER.error(f"Device | Error while disarming the system: {err.response.text}")
            raise err
        except LockError as err:
            _LOGGER.error(f"Device | Error while acquiring the system lock: {err}")
            raise err
        except CodeError as err:
            _LOGGER.error(f"Device | Credentials (alarm code) is incorrect: {err}")
            raise err
