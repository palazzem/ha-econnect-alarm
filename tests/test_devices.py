import pytest
from elmo import query as q
from elmo.api.exceptions import CodeError, CredentialError, LockError, ParseError
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMED_VACATION,
    STATE_ALARM_DISARMED,
    STATE_UNAVAILABLE,
)
from requests.exceptions import HTTPError

from custom_components.econnect_alarm.const import (
    CONF_AREAS_ARM_HOME,
    CONF_AREAS_ARM_NIGHT,
    CONF_AREAS_ARM_VACATION,
)
from custom_components.econnect_alarm.devices import AlarmDevice


def test_device_constructor(client):
    """Should initialize defaults attributes to run properly."""
    device = AlarmDevice(client)
    # Test
    assert device._connection == client
    assert device._lastIds == {q.SECTORS: 0, q.INPUTS: 0}
    assert device._sectors_home == []
    assert device._sectors_night == []
    assert device._sectors_vacation == []
    assert device.state == STATE_UNAVAILABLE
    assert device.sectors_armed == {}
    assert device.sectors_disarmed == {}
    assert device.inputs_alerted == {}
    assert device.inputs_wait == {}


def test_device_constructor_with_config(client):
    """Should initialize defaults attributes to run properly."""
    config = {
        CONF_AREAS_ARM_HOME: "3, 4",
        CONF_AREAS_ARM_NIGHT: "1, 2, 3",
        CONF_AREAS_ARM_VACATION: "5, 3",
    }
    device = AlarmDevice(client, config=config)
    # Test
    assert device._connection == client
    assert device._lastIds == {q.SECTORS: 0, q.INPUTS: 0}
    assert device._sectors_home == [3, 4]
    assert device._sectors_night == [1, 2, 3]
    assert device._sectors_vacation == [5, 3]
    assert device.state == STATE_UNAVAILABLE
    assert device.sectors_armed == {}
    assert device.sectors_disarmed == {}
    assert device.inputs_alerted == {}
    assert device.inputs_wait == {}


def test_device_connect(client, mocker):
    """Should call authentication endpoints and update internal state."""
    device = AlarmDevice(client)
    mocker.spy(device._connection, "auth")
    # Test
    device.connect("username", "password")
    assert device._connection.auth.call_count == 1
    assert "username" == device._connection.auth.call_args[0][0]
    assert "password" == device._connection.auth.call_args[0][1]


def test_device_connect_error(client, mocker):
    """Should handle (log) authentication errors (not 2xx)."""
    device = AlarmDevice(client)
    mocker.patch.object(device._connection, "auth")
    device._connection.auth.side_effect = HTTPError("Unable to communicate with e-Connect")
    # Test
    with pytest.raises(HTTPError):
        device.connect("username", "password")
    assert device._connection.auth.call_count == 1


def test_device_connect_credential_error(client, mocker):
    """Should handle (log) credential errors (401/403)."""
    device = AlarmDevice(client)
    mocker.patch.object(device._connection, "auth")
    device._connection.auth.side_effect = CredentialError("Incorrect username and/or password")
    # Test
    with pytest.raises(CredentialError):
        device.connect("username", "password")
    assert device._connection.auth.call_count == 1


def test_device_has_updates(client, mocker):
    """Should call the client polling system passing the internal state."""
    device = AlarmDevice(client)
    device.connect("username", "password")
    device._lastIds[q.SECTORS] = 20
    device._lastIds[q.INPUTS] = 20
    mocker.spy(device._connection, "poll")
    # Test
    device.has_updates()
    assert device._connection.poll.call_count == 1
    assert {9: 20, 10: 20} in device._connection.poll.call_args[0]


def test_device_has_updates_ids_immutable(client, mocker):
    """Device internal ids must be immutable."""

    def bad_poll(ids):
        ids[q.SECTORS] = 0
        ids[q.INPUTS] = 0

    device = AlarmDevice(client)
    device._lastIds = {q.SECTORS: 4, q.INPUTS: 42}
    mocker.patch.object(device._connection, "poll")
    device._connection.poll.side_effect = bad_poll
    # Test
    device.has_updates()
    assert device._connection.poll.call_count == 1
    assert {9: 4, 10: 42} == device._lastIds


def test_device_has_updates_errors(client, mocker):
    """Should handle (log) polling errors."""
    device = AlarmDevice(client)
    mocker.patch.object(device._connection, "poll")
    device._connection.poll.side_effect = HTTPError("Unable to communicate with e-Connect")
    # Test
    with pytest.raises(HTTPError):
        device.has_updates()
    assert device._connection.poll.call_count == 1
    assert {9: 0, 10: 0} == device._lastIds


def test_device_has_updates_parse_errors(client, mocker):
    """Should handle (log) polling errors."""
    device = AlarmDevice(client)
    mocker.patch.object(device._connection, "poll")
    device._connection.poll.side_effect = ParseError("Error parsing the poll response")
    # Test
    with pytest.raises(ParseError):
        device.has_updates()
    assert device._connection.poll.call_count == 1
    assert {9: 0, 10: 0} == device._lastIds


def test_device_update_success(client, mocker):
    """Should check store the e-connect System status in the device object."""
    device = AlarmDevice(client)
    mocker.spy(device._connection, "query")
    sectors_armed = {
        0: {"id": 1, "index": 0, "element": 1, "excluded": False, "status": True, "name": "S1 Living Room"},
        1: {"id": 2, "index": 1, "element": 2, "excluded": False, "status": True, "name": "S2 Bedroom"},
    }
    sectors_disarmed = {
        2: {"id": 3, "index": 2, "element": 3, "excluded": False, "status": False, "name": "S3 Outdoor"}
    }
    inputs_alerted = {
        0: {"id": 1, "index": 0, "element": 1, "excluded": False, "status": True, "name": "Entryway Sensor"},
        1: {"id": 2, "index": 1, "element": 2, "excluded": False, "status": True, "name": "Outdoor Sensor 1"},
    }
    inputs_wait = {
        2: {"id": 3, "index": 2, "element": 3, "excluded": True, "status": False, "name": "Outdoor Sensor 2"}
    }
    device.connect("username", "password")
    # Test
    device.update()
    assert device._connection.query.call_count == 2
    assert device.sectors_armed == sectors_armed
    assert device.sectors_disarmed == sectors_disarmed
    assert device.inputs_alerted == inputs_alerted
    assert device.inputs_wait == inputs_wait
    assert device._lastIds == {
        q.SECTORS: 4,
        q.INPUTS: 42,
    }


def test_device_update_http_error(client, mocker):
    """Tests if device's update method raises HTTPError when querying."""
    device = AlarmDevice(client)
    mocker.patch.object(device._connection, "query", side_effect=HTTPError("HTTP Error"))
    with pytest.raises(HTTPError):
        device.update()


def test_device_update_parse_error(client, mocker):
    """Tests if update method raises ParseError when querying."""
    device = AlarmDevice(client)
    mocker.patch.object(device._connection, "query", side_effect=ParseError("Parse Error"))
    with pytest.raises(ParseError):
        device.update()


def test_device_update_state_machine_armed(client, mocker):
    """Should check if the state machine is properly updated after calling update()."""
    device = AlarmDevice(client)
    mocker.patch.object(device._connection, "query")
    device._connection.query.side_effect = [
        {
            "last_id": 3,
            "sectors": {
                0: {"id": 1, "index": 0, "element": 1, "excluded": False, "status": True, "name": "S1 Living Room"},
                1: {"id": 2, "index": 1, "element": 2, "excluded": False, "status": True, "name": "S2 Bedroom"},
                2: {"id": 3, "index": 2, "element": 3, "excluded": False, "status": False, "name": "S3 Outdoor"},
            },
        },
        {
            "last_id": 3,
            "inputs": {
                0: {"id": 1, "index": 0, "element": 1, "excluded": False, "status": True, "name": "Entryway Sensor"},
                1: {"id": 2, "index": 1, "element": 2, "excluded": False, "status": True, "name": "Outdoor Sensor 1"},
                2: {"id": 3, "index": 2, "element": 3, "excluded": True, "status": False, "name": "Outdoor Sensor 2"},
            },
        },
    ]
    # Test
    device.update()
    assert device.state == "armed_away"


def test_device_update_state_machine_disarmed(client, mocker):
    """Should check if the state machine is properly updated after calling update()."""
    device = AlarmDevice(client)
    mocker.patch.object(device._connection, "query")
    device._connection.query.side_effect = [
        {
            "last_id": 3,
            "sectors": {
                0: {"id": 1, "index": 0, "element": 1, "excluded": False, "status": False, "name": "S1 Living Room"},
                1: {"id": 2, "index": 1, "element": 2, "excluded": False, "status": False, "name": "S2 Bedroom"},
                2: {"id": 3, "index": 2, "element": 3, "excluded": False, "status": False, "name": "S3 Outdoor"},
            },
        },
        {
            "last_id": 3,
            "inputs": {
                0: {"id": 1, "index": 0, "element": 1, "excluded": False, "status": True, "name": "Entryway Sensor"},
                1: {"id": 2, "index": 1, "element": 2, "excluded": False, "status": True, "name": "Outdoor Sensor 1"},
                2: {"id": 3, "index": 2, "element": 3, "excluded": True, "status": False, "name": "Outdoor Sensor 2"},
            },
        },
    ]
    # Test
    device.update()
    assert device.state == "disarmed"


@pytest.mark.xfail
def test_device_update_query_not_valid(client, mocker):
    """Should not crash if an exception is raised."""
    device = AlarmDevice(client)
    mocker.patch.object(device._connection, "query")
    device._connection.query.side_effect = Exception("Unexpected")
    # Test
    assert device.update() is None


def test_device_arm_success(client, mocker):
    """Should arm the e-connect system using the underlying client."""
    device = AlarmDevice(client)
    mocker.spy(device._connection, "lock")
    mocker.spy(device._connection, "arm")
    # Test
    device._connection._session_id = "test"
    device.arm("1234", sectors=[4])
    assert device._connection.lock.call_count == 1
    assert device._connection.arm.call_count == 1
    assert "1234" in device._connection.lock.call_args[0]
    assert {"sectors": [4]} == device._connection.arm.call_args[1]


def test_device_arm_error(client, mocker):
    """Should handle (log) connection errors."""
    device = AlarmDevice(client)
    mocker.spy(device._connection, "lock")
    mocker.spy(device._connection, "arm")
    device._connection.lock.side_effect = HTTPError("Unable to communicate with e-Connect")
    device._connection._session_id = "test"
    # Test
    with pytest.raises(HTTPError):
        device.arm("1234", sectors=[4])
    assert device._connection.lock.call_count == 1
    assert device._connection.arm.call_count == 0


def test_device_arm_lock_error(client, mocker):
    """Should handle (log) locking errors."""
    device = AlarmDevice(client)
    mocker.spy(device._connection, "lock")
    mocker.spy(device._connection, "arm")
    device._connection.lock.side_effect = LockError("Unable to acquire the lock")
    device._connection._session_id = "test"
    # Test
    with pytest.raises(LockError):
        device.arm("1234", sectors=[4])
    assert device._connection.lock.call_count == 1
    assert device._connection.arm.call_count == 0


def test_device_arm_code_error(client, mocker):
    """Should handle (log) code errors."""
    device = AlarmDevice(client)
    mocker.spy(device._connection, "lock")
    mocker.spy(device._connection, "arm")
    device._connection.lock.side_effect = CodeError("Code is incorrect")
    device._connection._session_id = "test"
    # Test
    with pytest.raises(CodeError):
        device.arm("1234", sectors=[4])
    assert device._connection.lock.call_count == 1
    assert device._connection.arm.call_count == 0


def test_device_disarm_success(client, mocker):
    """Should disarm the e-connect system using the underlying client."""
    device = AlarmDevice(client)
    mocker.spy(device._connection, "lock")
    mocker.spy(device._connection, "disarm")
    # Test
    device._connection._session_id = "test"
    device.disarm("1234", sectors=[4])

    assert device._connection.lock.call_count == 1
    assert device._connection.disarm.call_count == 1
    assert "1234" in device._connection.lock.call_args[0]
    assert {"sectors": [4]} == device._connection.disarm.call_args[1]


def test_device_disarm_error(client, mocker):
    """Should handle (log) connection errors."""
    device = AlarmDevice(client)
    mocker.spy(device._connection, "lock")
    mocker.spy(device._connection, "disarm")
    device._connection.lock.side_effect = HTTPError("Unable to communicate with e-Connect")
    device._connection._session_id = "test"
    # Test
    with pytest.raises(HTTPError):
        device.disarm("1234", sectors=[4])
    assert device._connection.lock.call_count == 1
    assert device._connection.disarm.call_count == 0


def test_device_disarm_lock_error(client, mocker):
    """Should handle (log) locking errors."""
    device = AlarmDevice(client)
    mocker.spy(device._connection, "lock")
    mocker.spy(device._connection, "disarm")
    device._connection.lock.side_effect = LockError("Unable to acquire the lock")
    device._connection._session_id = "test"
    # Test
    with pytest.raises(LockError):
        device.disarm("1234", sectors=[4])
    assert device._connection.lock.call_count == 1
    assert device._connection.disarm.call_count == 0


def test_device_disarm_code_error(client, mocker):
    """Should handle (log) code errors."""
    device = AlarmDevice(client)
    mocker.spy(device._connection, "lock")
    mocker.spy(device._connection, "disarm")
    device._connection.lock.side_effect = CodeError("Code is incorrect")
    device._connection._session_id = "test"
    # Test
    with pytest.raises(CodeError):
        device.disarm("1234", sectors=[4])
    assert device._connection.lock.call_count == 1
    assert device._connection.disarm.call_count == 0


def test_get_state_no_sectors_armed(client):
    """Test when no sectors are armed."""
    device = AlarmDevice(client)
    device._sectors_home = []
    device._sectors_night = []
    device.sectors_armed = {}
    # Test
    assert device.get_state() == STATE_ALARM_DISARMED


def test_get_state_armed_home(client):
    """Test when sectors are armed for home."""
    device = AlarmDevice(client)
    device._sectors_home = [1, 2, 3]
    device.sectors_armed = {
        0: {"id": 1, "index": 0, "element": 1, "excluded": False, "status": True, "name": "S1 Living Room"},
        1: {"id": 2, "index": 1, "element": 2, "excluded": False, "status": True, "name": "S2 Bedroom"},
        2: {"id": 3, "index": 2, "element": 3, "excluded": False, "status": True, "name": "S3 Outdoor"},
    }
    # Test
    assert device.get_state() == STATE_ALARM_ARMED_HOME


def test_get_state_armed_home_out_of_order(client):
    """Test when sectors are armed for home (out of order)."""
    device = AlarmDevice(client)
    device._sectors_home = [2, 1, 3]
    device.sectors_armed = {
        0: {"id": 1, "index": 0, "element": 3, "excluded": False, "status": True, "name": "S1 Living Room"},
        1: {"id": 2, "index": 1, "element": 1, "excluded": False, "status": True, "name": "S2 Bedroom"},
        2: {"id": 3, "index": 2, "element": 2, "excluded": False, "status": True, "name": "S3 Outdoor"},
    }
    # Test
    assert device.get_state() == STATE_ALARM_ARMED_HOME


def test_get_state_armed_night(client):
    """Test when sectors are armed for night."""
    device = AlarmDevice(client)
    device._sectors_night = [4, 5, 6]
    device.sectors_armed = {
        0: {"id": 1, "index": 0, "element": 4, "excluded": False, "status": True, "name": "S1 Living Room"},
        1: {"id": 2, "index": 1, "element": 5, "excluded": False, "status": True, "name": "S2 Bedroom"},
        2: {"id": 3, "index": 2, "element": 6, "excluded": False, "status": True, "name": "S3 Outdoor"},
    }
    # Test (out of order keys to test sorting)
    assert device.get_state() == STATE_ALARM_ARMED_NIGHT


def test_get_state_armed_night_out_of_order(client):
    """Test when sectors are armed for night (out of order)."""
    device = AlarmDevice(client)
    device._sectors_night = [5, 6, 4]
    device.sectors_armed = {
        0: {"id": 1, "index": 0, "element": 6, "excluded": False, "status": True, "name": "S1 Living Room"},
        1: {"id": 2, "index": 1, "element": 4, "excluded": False, "status": True, "name": "S2 Bedroom"},
        2: {"id": 3, "index": 2, "element": 5, "excluded": False, "status": True, "name": "S3 Outdoor"},
    }
    # Test
    assert device.get_state() == STATE_ALARM_ARMED_NIGHT


def test_get_state_armed_vacation(client):
    """Test when sectors are armed for vacation."""
    device = AlarmDevice(client)
    device._sectors_vacation = [4, 5, 6]
    device.sectors_armed = {
        0: {"id": 1, "index": 0, "element": 4, "excluded": False, "status": True, "name": "S1 Living Room"},
        1: {"id": 2, "index": 1, "element": 5, "excluded": False, "status": True, "name": "S2 Bedroom"},
        2: {"id": 3, "index": 2, "element": 6, "excluded": False, "status": True, "name": "S3 Outdoor"},
    }
    # Test (out of order keys to test sorting)
    assert device.get_state() == STATE_ALARM_ARMED_VACATION


def test_get_state_armed_vacation_out_of_order(client):
    """Test when sectors are armed for vacation (out of order)."""
    device = AlarmDevice(client)
    device._sectors_vacation = [5, 6, 4]
    device.sectors_armed = {
        0: {"id": 1, "index": 0, "element": 6, "excluded": False, "status": True, "name": "S1 Living Room"},
        1: {"id": 2, "index": 1, "element": 4, "excluded": False, "status": True, "name": "S2 Bedroom"},
        2: {"id": 3, "index": 2, "element": 5, "excluded": False, "status": True, "name": "S3 Outdoor"},
    }
    # Test
    assert device.get_state() == STATE_ALARM_ARMED_VACATION


def test_get_state_armed_away(client):
    """Test when sectors are armed but don't match home or night."""
    device = AlarmDevice(client)
    device._sectors_home = [1, 2, 3]
    device._sectors_night = [4, 5, 6]
    device._sectors_vacation = [4, 2]
    device.sectors_armed = {
        0: {"id": 1, "index": 0, "element": 1, "excluded": False, "status": True, "name": "S1 Living Room"},
        1: {"id": 2, "index": 1, "element": 2, "excluded": False, "status": True, "name": "S2 Bedroom"},
        2: {"id": 3, "index": 2, "element": 4, "excluded": False, "status": True, "name": "S3 Outdoor"},
    }
    # Test
    assert device.get_state() == STATE_ALARM_ARMED_AWAY


def test_get_state_armed_mixed(client):
    """Test when some sectors from home and night are armed."""
    device = AlarmDevice(client)
    device._sectors_home = [1, 2, 3]
    device._sectors_night = [4, 5, 6]
    device.sectors_armed = {
        0: {"id": 1, "index": 0, "element": 1, "excluded": False, "status": True, "name": "S1 Living Room"},
        1: {"id": 2, "index": 1, "element": 2, "excluded": False, "status": True, "name": "S2 Bedroom"},
        2: {"id": 3, "index": 2, "element": 3, "excluded": False, "status": True, "name": "S3 Outdoor"},
        3: {"id": 4, "index": 3, "element": 5, "excluded": False, "status": True, "name": "S5 Perimeter"},
    }
    # Test
    assert device.get_state() == STATE_ALARM_ARMED_AWAY
