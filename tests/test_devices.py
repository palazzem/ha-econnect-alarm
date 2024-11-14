import pytest
import responses
from elmo import query as q
from elmo.api.exceptions import CodeError, CredentialError, LockError, ParseError
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from requests.exceptions import HTTPError
from requests.models import Response

from custom_components.econnect_metronet.binary_sensor import SectorBinarySensor
from custom_components.econnect_metronet.const import (
    CONF_AREAS_ARM_AWAY,
    CONF_AREAS_ARM_HOME,
    CONF_AREAS_ARM_NIGHT,
    CONF_AREAS_ARM_VACATION,
    CONF_MANAGE_SECTORS,
)
from custom_components.econnect_metronet.devices import AlarmDevice

from .fixtures import responses as r


def test_device_constructor(client):
    """Should initialize defaults attributes to run properly."""
    device = AlarmDevice(client)
    # Test
    assert device.connected is False
    assert device._connection == client
    assert device._inventory == {}
    assert device._sectors == {}
    assert device._last_ids == {10: 0, 9: 0, 11: 0, 12: 0}
    assert device._managed_sectors == []
    assert device._sectors_away == []
    assert device._sectors_home == []
    assert device._sectors_night == []
    assert device._sectors_vacation == []
    assert device.state is None


def test_device_constructor_with_config(client):
    """Should initialize defaults attributes to run properly."""
    config = {
        CONF_AREAS_ARM_AWAY: [1, 2, 3, 4, 5],
        CONF_AREAS_ARM_HOME: [3, 4],
        CONF_AREAS_ARM_NIGHT: [1, 2, 3],
        CONF_AREAS_ARM_VACATION: [5, 3],
        CONF_MANAGE_SECTORS: [1, 2, 3, 4, 5],
    }
    device = AlarmDevice(client, config=config)
    # Test
    assert device.connected is False
    assert device._connection == client
    assert device._inventory == {}
    assert device._sectors == {}
    assert device._last_ids == {10: 0, 9: 0, 11: 0, 12: 0}
    assert device._managed_sectors == [1, 2, 3, 4, 5]
    assert device._sectors_away == [1, 2, 3, 4, 5]
    assert device._sectors_home == [3, 4]
    assert device._sectors_night == [1, 2, 3]
    assert device._sectors_vacation == [5, 3]
    assert device.state is None


def test_device_constructor_with_config_empty(client):
    """Should initialize defaults attributes to run properly."""
    config = {
        CONF_AREAS_ARM_AWAY: None,
        CONF_AREAS_ARM_HOME: None,
        CONF_AREAS_ARM_NIGHT: None,
        CONF_AREAS_ARM_VACATION: None,
        CONF_MANAGE_SECTORS: None,
    }
    device = AlarmDevice(client, config=config)
    # Test
    assert device.connected is False
    assert device._connection == client
    assert device._inventory == {}
    assert device._sectors == {}
    assert device._last_ids == {10: 0, 9: 0, 11: 0, 12: 0}
    assert device._managed_sectors == []
    assert device._sectors_away == []
    assert device._sectors_home == []
    assert device._sectors_night == []
    assert device._sectors_vacation == []
    assert device.state is None


class TestItemInputs:
    def test_without_status(self, alarm_device):
        """Verify that querying items without specifying a status works correctly"""
        alarm_device.connect("username", "password")
        inputs = {
            0: {"id": 1, "index": 0, "element": 1, "excluded": False, "status": True, "name": "Entryway Sensor"},
            1: {"id": 2, "index": 1, "element": 2, "excluded": False, "status": True, "name": "Outdoor Sensor 1"},
            2: {"id": 3, "index": 2, "element": 3, "excluded": True, "status": False, "name": "Outdoor Sensor 2"},
        }
        # Test
        alarm_device.update()
        assert dict(alarm_device.items(q.INPUTS)) == inputs

    def test_with_status(self, alarm_device):
        """Verify that querying items with specifying a status works correctly"""
        alarm_device.connect("username", "password")
        # Test
        alarm_device.update()
        assert dict(alarm_device.items(q.INPUTS, status=False)) == {
            2: {"id": 3, "index": 2, "element": 3, "excluded": True, "status": False, "name": "Outdoor Sensor 2"}
        }

    def test_without_inventory(self, alarm_device):
        """Verify that querying items without inventory populated works correctly"""
        alarm_device._inventory = {}
        # Test
        assert dict(alarm_device.items(q.INPUTS, status=False)) == {}

    def test_with_empty_query(self, alarm_device):
        """Verify that querying items with empty query works correctly"""
        alarm_device._inventory = {10: {}}
        # Test
        assert dict(alarm_device.items(q.INPUTS, status=False)) == {}


class TestItemSectors:
    def test_without_status(self, alarm_device):
        """Verify that querying items without specifying a status works correctly"""
        alarm_device.connect("username", "password")
        sectors = {
            0: {"element": 1, "activable": True, "id": 1, "index": 0, "name": "S1 Living Room", "status": True},
            1: {"element": 2, "activable": True, "id": 2, "index": 1, "name": "S2 Bedroom", "status": True},
            2: {"element": 3, "activable": False, "id": 3, "index": 2, "name": "S3 Outdoor", "status": False},
        }
        # Test
        alarm_device.update()
        assert dict(alarm_device.items(q.SECTORS)) == sectors

    def test_with_status(self, alarm_device):
        """Verify that querying items with specifying a status works correctly"""
        alarm_device.connect("username", "password")
        # Test
        alarm_device.update()
        assert dict(alarm_device.items(q.SECTORS, status=False)) == {
            2: {"element": 3, "activable": False, "id": 3, "index": 2, "name": "S3 Outdoor", "status": False}
        }

    def test_without_inventory(self, alarm_device):
        """Verify that querying items without inventory populated works correctly"""
        alarm_device._inventory = {}
        # Test
        assert dict(alarm_device.items(q.SECTORS, status=False)) == {}

    def test_with_empty_query(self, alarm_device):
        """Verify that querying items with empty query works correctly"""
        alarm_device._inventory = {10: {}}
        # Test
        assert dict(alarm_device.items(q.SECTORS, status=False)) == {}


class TestItemOutputs:
    def test_without_status(self, alarm_device):
        """Verify that querying items without specifying a status works correctly"""
        alarm_device.connect("username", "password")
        outputs = {
            0: {
                "element": 1,
                "control_denied_to_users": False,
                "do_not_require_authentication": True,
                "id": 1,
                "index": 0,
                "name": "Output 1",
                "status": True,
            },
            1: {
                "element": 2,
                "control_denied_to_users": False,
                "do_not_require_authentication": False,
                "id": 2,
                "index": 1,
                "name": "Output 2",
                "status": True,
            },
            2: {
                "element": 3,
                "control_denied_to_users": True,
                "do_not_require_authentication": False,
                "id": 3,
                "index": 2,
                "name": "Output 3",
                "status": False,
            },
        }
        # Test
        alarm_device.update()
        assert dict(alarm_device.items(q.OUTPUTS)) == outputs

    def test_with_status(self, alarm_device):
        """Verify that querying items with specifying a status works correctly"""
        alarm_device.connect("username", "password")
        # Test
        alarm_device.update()
        assert dict(alarm_device.items(q.OUTPUTS, status=False)) == {
            2: {
                "element": 3,
                "control_denied_to_users": True,
                "do_not_require_authentication": False,
                "id": 3,
                "index": 2,
                "name": "Output 3",
                "status": False,
            }
        }

    def test_without_inventory(self, alarm_device):
        """Verify that querying items without inventory populated works correctly"""
        alarm_device._inventory = {}
        # Test
        assert dict(alarm_device.items(q.OUTPUTS, status=False)) == {}

    def test_with_empty_query(self, alarm_device):
        """Verify that querying items with empty query works correctly"""
        alarm_device._inventory = {12: {}}
        # Test
        assert dict(alarm_device.items(q.OUTPUTS, status=False)) == {}


class TestItemAlerts:
    def test_without_status(self, alarm_device):
        """Verify that querying items without specifying a status works correctly"""
        alarm_device.connect("username", "password")
        alerts = {
            0: {"name": "alarm_led", "status": 0},
            1: {"name": "anomalies_led", "status": 1},
            2: {"name": "device_failure", "status": 0},
            3: {"name": "device_low_battery", "status": 0},
            4: {"name": "device_no_power", "status": 0},
            5: {"name": "device_no_supervision", "status": 0},
            6: {"name": "device_system_block", "status": 0},
            7: {"name": "device_tamper", "status": 1},
            8: {"name": "gsm_anomaly", "status": 0},
            9: {"name": "gsm_low_balance", "status": 0},
            10: {"name": "has_anomaly", "status": False},
            11: {"name": "input_alarm", "status": 0},
            12: {"name": "input_bypass", "status": 0},
            13: {"name": "input_failure", "status": 0},
            14: {"name": "input_low_battery", "status": 0},
            15: {"name": "input_no_supervision", "status": 0},
            16: {"name": "inputs_led", "status": 2},
            17: {"name": "module_registration", "status": 0},
            18: {"name": "panel_low_battery", "status": 0},
            19: {"name": "panel_no_power", "status": 0},
            20: {"name": "panel_tamper", "status": 0},
            21: {"name": "pstn_anomaly", "status": 0},
            22: {"name": "rf_interference", "status": 0},
            23: {"name": "system_test", "status": 0},
            24: {"name": "tamper_led", "status": 0},
        }
        # Test
        alarm_device.update()
        assert dict(alarm_device.items(q.ALERTS)) == alerts

    def test_with_status_1(self, alarm_device):
        """Verify that querying items with specifying a status works correctly"""
        alarm_device.connect("username", "password")
        alerts_1 = {
            1: {"name": "anomalies_led", "status": 1},
            7: {"name": "device_tamper", "status": 1},
        }
        # Test
        alarm_device.update()
        assert dict(alarm_device.items(q.ALERTS, status=1)) == alerts_1

    def test_with_status_true(self, alarm_device):
        """Verify that querying items with specifying a status works correctly"""
        alarm_device.connect("username", "password")
        alerts_true = {
            1: {"name": "anomalies_led", "status": True},
            7: {"name": "device_tamper", "status": True},
        }
        # Test
        alarm_device.update()
        assert dict(alarm_device.items(q.ALERTS, status=1)) == alerts_true

    def test_without_inventory(self, alarm_device):
        """Verify that querying items without inventory populated works correctly"""
        alarm_device._inventory = {}
        # Test
        assert dict(alarm_device.items(q.ALERTS, status=False)) == {}

    def test_with_empty_query(self, alarm_device):
        """Verify that querying items with empty query works correctly"""
        alarm_device._inventory = {11: {}}
        # Test
        assert dict(alarm_device.items(q.ALERTS, status=False)) == {}


class TestItemPanel:
    def test_without_status(self, alarm_device):
        """Verify that querying items without specifying a status works correctly"""
        alarm_device.connect("username", "password")
        details = {
            "description": "T-800 1.0.1",
            "last_connection": "01/01/1984 13:27:28",
            "last_disconnection": "01/10/1984 13:27:18",
            "major": 1,
            "minor": 0,
            "source_ip": "10.0.0.1",
            "connection_type": "EthernetWiFi",
            "device_class": 92,
            "revision": 1,
            "build": 1,
            "brand": 0,
            "language": 0,
            "areas": 4,
            "sectors_per_area": 4,
            "total_sectors": 16,
            "inputs": 24,
            "outputs": 24,
            "operators": 64,
            "sectors_in_use": [
                True,
                True,
                True,
                True,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
            ],
            "model": "T-800",
            "login_without_user_id": True,
            "additional_info_supported": 1,
            "is_fire_panel": False,
        }
        # Test
        alarm_device.update()
        assert dict(alarm_device.items(q.PANEL)) == details

    def test_without_inventory(self, alarm_device):
        """Verify that querying items without inventory populated works correctly"""
        alarm_device._inventory = {}
        # Test
        assert dict(alarm_device.items(q.PANEL)) == {}

    def test_with_empty_query(self, alarm_device):
        """Verify that querying items with empty query works correctly"""
        alarm_device._inventory = {0: {}}
        # Test
        assert dict(alarm_device.items(q.PANEL)) == {}


def test_device_connect(client, mocker):
    """Should call authentication endpoints and update internal state."""
    device = AlarmDevice(client)
    mocker.spy(device._connection, "auth")
    # Test
    device.connect("username", "password")
    assert device._connection.auth.call_count == 1
    assert "username" == device._connection.auth.call_args[0][0]
    assert "password" == device._connection.auth.call_args[0][1]
    assert device.connected is True


def test_device_connect_error(client, mocker):
    """Should handle (log) authentication errors (not 2xx)."""
    device = AlarmDevice(client)
    mocker.patch.object(device._connection, "auth")
    device._connection.auth.side_effect = HTTPError("Unable to communicate with e-Connect")
    # Test
    with pytest.raises(HTTPError):
        device.connect("username", "password")
    assert device._connection.auth.call_count == 1
    assert device.connected is False


def test_device_connect_credential_error(client, mocker):
    """Should handle (log) credential errors (401/403)."""
    device = AlarmDevice(client)
    mocker.patch.object(device._connection, "auth")
    device._connection.auth.side_effect = CredentialError("Incorrect username and/or password")
    # Test
    with pytest.raises(CredentialError):
        device.connect("username", "password")
    assert device._connection.auth.call_count == 1
    assert device.connected is False


def test_device_has_updates(client, mocker):
    """Should call the client polling system passing the internal state."""
    device = AlarmDevice(client)
    device.connect("username", "password")
    device._last_ids[q.SECTORS] = 20
    device._last_ids[q.INPUTS] = 20
    device._last_ids[q.OUTPUTS] = 20
    device._last_ids[q.ALERTS] = 20
    mocker.spy(device._connection, "poll")
    # Test
    device.has_updates()
    assert device._connection.poll.call_count == 1
    assert {9: 20, 10: 20, 11: 20, 12: 20} in device._connection.poll.call_args[0]


def test_device_has_updates_ids_immutable(client, mocker):
    """Device internal ids must be immutable."""

    def bad_poll(ids):
        ids[q.SECTORS] = 0
        ids[q.INPUTS] = 0

    device = AlarmDevice(client)
    device.connect("username", "password")
    device._last_ids = {q.SECTORS: 4, q.INPUTS: 42}
    mocker.patch.object(device._connection, "poll")
    device._connection.poll.side_effect = bad_poll
    # Test
    device.has_updates()
    assert device._connection.poll.call_count == 1
    assert {9: 4, 10: 42} == device._last_ids


def test_device_has_updates_errors(client, mocker):
    """Should handle (log) polling errors."""
    device = AlarmDevice(client)
    device.connect("username", "password")
    mocker.patch.object(device._connection, "poll")
    device._connection.poll.side_effect = HTTPError(response=Response())
    # Test
    with pytest.raises(HTTPError):
        device.has_updates()
    assert device._connection.poll.call_count == 1
    assert {9: 0, 10: 0, 11: 0, 12: 0} == device._last_ids


def test_device_has_updates_parse_errors(client, mocker):
    """Should handle (log) polling errors."""
    device = AlarmDevice(client)
    device.connect("username", "password")
    mocker.patch.object(device._connection, "poll")
    device._connection.poll.side_effect = ParseError("Error parsing the poll response")
    # Test
    with pytest.raises(ParseError):
        device.has_updates()
    assert device._connection.poll.call_count == 1
    assert {9: 0, 10: 0, 11: 0, 12: 0} == device._last_ids


def test_device_update_success(client, mocker):
    """Should check store the e-connect System status in the device object."""
    device = AlarmDevice(client)
    mocker.spy(device._connection, "query")
    device.connect("username", "password")
    # Test
    device.update()
    assert device._connection.query.call_count == 5
    assert device._last_ids == {
        0: 0,
        9: 4,
        10: 42,
        11: 1,
        12: 4,
    }


def test_device_inventory_update_success(client, mocker):
    """Should check store the e-connect System status in the inventory device object."""
    device = AlarmDevice(client)
    mocker.spy(device._connection, "query")
    inventory = {
        0: {
            "additional_info_supported": 1,
            "areas": 4,
            "brand": 0,
            "build": 1,
            "connection_type": "EthernetWiFi",
            "description": "T-800 1.0.1",
            "device_class": 92,
            "inputs": 24,
            "is_fire_panel": False,
            "language": 0,
            "last_connection": "01/01/1984 13:27:28",
            "last_disconnection": "01/10/1984 13:27:18",
            "login_without_user_id": True,
            "major": 1,
            "minor": 0,
            "model": "T-800",
            "operators": 64,
            "outputs": 24,
            "revision": 1,
            "sectors_in_use": [
                True,
                True,
                True,
                True,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
            ],
            "sectors_per_area": 4,
            "source_ip": "10.0.0.1",
            "total_sectors": 16,
        },
        9: {
            0: {"element": 1, "activable": True, "id": 1, "index": 0, "name": "S1 Living Room", "status": True},
            1: {"element": 2, "activable": True, "id": 2, "index": 1, "name": "S2 Bedroom", "status": True},
            2: {"element": 3, "activable": False, "id": 3, "index": 2, "name": "S3 Outdoor", "status": False},
        },
        10: {
            0: {"id": 1, "index": 0, "element": 1, "excluded": False, "status": True, "name": "Entryway Sensor"},
            1: {"id": 2, "index": 1, "element": 2, "excluded": False, "status": True, "name": "Outdoor Sensor 1"},
            2: {"id": 3, "index": 2, "element": 3, "excluded": True, "status": False, "name": "Outdoor Sensor 2"},
        },
        11: {
            0: {"name": "alarm_led", "status": 0},
            1: {"name": "anomalies_led", "status": 1},
            2: {"name": "device_failure", "status": 0},
            3: {"name": "device_low_battery", "status": 0},
            4: {"name": "device_no_power", "status": 0},
            5: {"name": "device_no_supervision", "status": 0},
            6: {"name": "device_system_block", "status": 0},
            7: {"name": "device_tamper", "status": 1},
            8: {"name": "gsm_anomaly", "status": 0},
            9: {"name": "gsm_low_balance", "status": 0},
            10: {"name": "has_anomaly", "status": False},
            11: {"name": "input_alarm", "status": 0},
            12: {"name": "input_bypass", "status": 0},
            13: {"name": "input_failure", "status": 0},
            14: {"name": "input_low_battery", "status": 0},
            15: {"name": "input_no_supervision", "status": 0},
            16: {"name": "inputs_led", "status": 2},
            17: {"name": "module_registration", "status": 0},
            18: {"name": "panel_low_battery", "status": 0},
            19: {"name": "panel_no_power", "status": 0},
            20: {"name": "panel_tamper", "status": 0},
            21: {"name": "pstn_anomaly", "status": 0},
            22: {"name": "rf_interference", "status": 0},
            23: {"name": "system_test", "status": 0},
            24: {"name": "tamper_led", "status": 0},
        },
        12: {
            0: {
                "element": 1,
                "control_denied_to_users": False,
                "do_not_require_authentication": True,
                "id": 1,
                "index": 0,
                "name": "Output 1",
                "status": True,
            },
            1: {
                "element": 2,
                "control_denied_to_users": False,
                "do_not_require_authentication": False,
                "id": 2,
                "index": 1,
                "name": "Output 2",
                "status": True,
            },
            2: {
                "element": 3,
                "control_denied_to_users": True,
                "do_not_require_authentication": False,
                "id": 3,
                "index": 2,
                "name": "Output 3",
                "status": False,
            },
        },
    }
    device.connect("username", "password")
    # Test
    device.update()
    assert device._inventory == inventory


def test_device_inventory_update_managed_sectors(alarm_device):
    # Ensure that only managed sectors are updated
    alarm_device._managed_sectors = [2, 3]
    # Test
    alarm_device.update()
    assert alarm_device._inventory[q.SECTORS] == {
        1: {"element": 2, "activable": True, "id": 2, "index": 1, "name": "S2 Bedroom", "status": True},
        2: {"element": 3, "activable": False, "id": 3, "index": 2, "name": "S3 Outdoor", "status": False},
    }


def test_device_inventory_update_after_connection_reset(mocker, alarm_device):
    # Ensure that after a connection reset (last_id == 1), the inventory is not updated
    # Regression test for: https://github.com/palazzem/ha-econnect-alarm/issues/148
    AREAS = """[
       {
           "Active": false,
           "ActivePartial": false,
           "Max": false,
           "Activable": false,
           "ActivablePartial": false,
           "InUse": true,
           "Id": 1,
           "Index": 0,
           "Element": 1,
           "CommandId": 0,
           "InProgress": false
       },
       {
           "Active": false,
           "ActivePartial": false,
           "Max": false,
           "Activable": false,
           "ActivablePartial": false,
           "InUse": true,
           "Id": 1,
           "Index": 1,
           "Element": 2,
           "CommandId": 0,
           "InProgress": false
       },
       {
           "Active": false,
           "ActivePartial": false,
           "Max": false,
           "Activable": false,
           "ActivablePartial": false,
           "InUse": true,
           "Id": 1,
           "Index": 2,
           "Element": 3,
           "CommandId": 0,
           "InProgress": false
       }
    ]"""
    # Test
    with responses.RequestsMock() as server:
        server.add(responses.POST, "https://example.com/api/areas", body=AREAS, status=200)
        server.add(responses.POST, "https://example.com/api/inputs", body=r.INPUTS, status=200)
        server.add(responses.POST, "https://example.com/api/outputs", body=r.OUTPUTS, status=200)
        server.add(responses.POST, "https://example.com/api/statusadv", body=r.STATUS, status=200)
        inventory = alarm_device.update()
        assert inventory[q.SECTORS][0]["status"] is True
        assert inventory[q.SECTORS][1]["status"] is True
        assert inventory[q.SECTORS][2]["status"] is False


class TestInputsView:
    def test_property_populated(self, alarm_device):
        """Should check if the device property is correctly populated"""
        inputs = {
            0: "Entryway Sensor",
            1: "Outdoor Sensor 1",
            2: "Outdoor Sensor 2",
        }
        # Test
        assert dict(alarm_device.inputs) == inputs

    def test_inventory_empty(self, alarm_device):
        """Ensure the property returns an empty dict if _inventory is empty"""
        # Test
        alarm_device._inventory = {}
        assert dict(alarm_device.inputs) == {}

    def test_input_property_empty(self, alarm_device):
        """Ensure the property returns an empty dict if inputs key is not in _inventory"""
        # Test
        alarm_device._inventory = {10: {}}
        assert dict(alarm_device.inputs) == {}


class TestSectorsView:
    def test_property_populated(self, alarm_device):
        """Should check if the device property is correctly populated"""
        sectors = {
            0: "S1 Living Room",
            1: "S2 Bedroom",
            2: "S3 Outdoor",
        }
        # Test
        assert dict(alarm_device.sectors) == sectors

    def test_inventory_empty(self, alarm_device):
        """Ensure the property returns an empty dict if _inventory is empty"""
        # Test
        alarm_device._inventory = {}
        assert dict(alarm_device.sectors) == {}

    def test_sectors_property_empty(self, alarm_device):
        """Ensure the property returns an empty dict if sectors key is not in _inventory"""
        # Test
        alarm_device._inventory = {9: {}}
        assert dict(alarm_device.sectors) == {}


class TestOutputsView:
    def test_property_populated(self, alarm_device):
        """Should check if the device property is correctly populated"""
        outputs = {
            0: "Output 1",
            1: "Output 2",
            2: "Output 3",
        }
        # Test
        assert dict(alarm_device.outputs) == outputs

    def test_inventory_empty(self, alarm_device):
        """Ensure the property returns an empty dict if _inventory is empty"""
        # Test
        alarm_device._inventory = {}
        assert dict(alarm_device.outputs) == {}

    def test_sectors_property_empty(self, alarm_device):
        """Ensure the property returns an empty dict if outputs key is not in _inventory"""
        # Test
        alarm_device._inventory = {12: {}}
        assert dict(alarm_device.outputs) == {}


class TestAlertsView:
    def test_property_populated(self, alarm_device):
        """Should check if the device property is correctly populated"""
        alerts = {
            0: "alarm_led",
            1: "anomalies_led",
            2: "device_failure",
            3: "device_low_battery",
            4: "device_no_power",
            5: "device_no_supervision",
            6: "device_system_block",
            7: "device_tamper",
            8: "gsm_anomaly",
            9: "gsm_low_balance",
            10: "has_anomaly",
            11: "input_alarm",
            12: "input_bypass",
            13: "input_failure",
            14: "input_low_battery",
            15: "input_no_supervision",
            16: "inputs_led",
            17: "module_registration",
            18: "panel_low_battery",
            19: "panel_no_power",
            20: "panel_tamper",
            21: "pstn_anomaly",
            22: "rf_interference",
            23: "system_test",
            24: "tamper_led",
        }
        # Test
        assert dict(alarm_device.alerts) == alerts

    def test_inventory_empty(self, alarm_device):
        """Ensure the property returns an empty dict if _inventory is empty"""
        # Test
        alarm_device._inventory = {}
        assert dict(alarm_device.alerts) == {}

    def test_alerts_property_empty(self, alarm_device):
        """Ensure the property returns an empty dict if alerts key is not in _inventory"""
        # Test
        alarm_device._inventory = {11: {}}
        assert dict(alarm_device.alerts) == {}


class TestPanelView:
    def test_property_populated(self, alarm_device):
        """Should check if the device property is correctly populated"""
        panel = {
            "description": "T-800 1.0.1",
            "last_connection": "01/01/1984 13:27:28",
            "last_disconnection": "01/10/1984 13:27:18",
            "major": 1,
            "minor": 0,
            "source_ip": "10.0.0.1",
            "connection_type": "EthernetWiFi",
            "device_class": 92,
            "revision": 1,
            "build": 1,
            "brand": 0,
            "language": 0,
            "areas": 4,
            "sectors_per_area": 4,
            "total_sectors": 16,
            "inputs": 24,
            "outputs": 24,
            "operators": 64,
            "sectors_in_use": [
                True,
                True,
                True,
                True,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
            ],
            "model": "T-800",
            "login_without_user_id": True,
            "additional_info_supported": 1,
            "is_fire_panel": False,
        }
        # Test
        assert dict(alarm_device.panel) == panel

    def test_inventory_empty(self, alarm_device):
        """Ensure the property returns an empty dict if _inventory is empty"""
        # Test
        alarm_device._inventory = {}
        assert dict(alarm_device.panel) == {}

    def test_sectors_property_empty(self, alarm_device):
        """Ensure the property returns an empty dict if outputs key is not in _inventory"""
        # Test
        alarm_device._inventory = {0: {}}
        assert dict(alarm_device.panel) == {}


class TestGetStatusInputs:
    def test_get_status_populated(self, alarm_device):
        """Should check if the device property is correctly populated"""
        # Test
        assert alarm_device.get_status(q.INPUTS, 2) is False

    def test_inventory_empty(self, alarm_device):
        """Ensure the property returns a KeyError if _inventory is empty"""
        # Test
        alarm_device._inventory = {}
        with pytest.raises(KeyError):
            assert alarm_device.get_status(q.INPUTS, 2)

    def test_alerts_property_empty(self, alarm_device):
        """Ensure the property returns a KeyError if inputs key is not in _inventory"""
        # Test
        alarm_device._inventory = {10: {}}
        with pytest.raises(KeyError):
            assert alarm_device.get_status(q.INPUTS, 2)


class TestGetStatusSectors:
    def test_get_status_populated(self, alarm_device):
        """Should check if the device property is correctly populated"""
        # Test
        assert alarm_device.get_status(q.SECTORS, 2) is False

    def test_inventory_empty(self, alarm_device):
        """Ensure the property returns a KeyError if _inventory is empty"""
        # Test
        alarm_device._inventory = {}
        with pytest.raises(KeyError):
            assert alarm_device.get_status(q.SECTORS, 2)

    def test_alerts_property_empty(self, alarm_device):
        """Ensure the property returns a KeyError if sectors key is not in _inventory"""
        # Test
        alarm_device._inventory = {9: {}}
        with pytest.raises(KeyError):
            assert alarm_device.get_status(q.SECTORS, 2)


class TestGetStatusOutputs:
    def test_get_status_populated(self, alarm_device):
        """Should check if the device property is correctly populated"""
        # Test
        assert alarm_device.get_status(q.OUTPUTS, 2) == 0

    def test_inventory_empty(self, alarm_device):
        """Ensure the property returns a KeyError if _inventory is empty"""
        # Test
        alarm_device._inventory = {}
        with pytest.raises(KeyError):
            assert alarm_device.get_status(q.OUTPUTS, 2)

    def test_alerts_property_empty(self, alarm_device):
        """Ensure the property returns a KeyError if alerts key is not in _inventory"""
        # Test
        alarm_device._inventory = {12: {}}
        with pytest.raises(KeyError):
            assert alarm_device.get_status(q.OUTPUTS, 2)


class TestGetStatusAlerts:
    def test_get_status_populated(self, alarm_device):
        """Should check if the device property is correctly populated"""
        # Test
        assert alarm_device.get_status(q.ALERTS, 2) == 0

    def test_inventory_empty(self, alarm_device):
        """Ensure the property returns a KeyError if _inventory is empty"""
        # Test
        alarm_device._inventory = {}
        with pytest.raises(KeyError):
            assert alarm_device.get_status(q.ALERTS, 2)

    def test_alerts_property_empty(self, alarm_device):
        """Ensure the property returns a KeyError if alerts key is not in _inventory"""
        # Test
        alarm_device._inventory = {11: {}}
        with pytest.raises(KeyError):
            assert alarm_device.get_status(q.ALERTS, 2)


def test_device_update_http_error(client, mocker):
    """Tests if device's update method raises HTTPError when querying."""
    device = AlarmDevice(client)
    mocker.patch.object(device._connection, "query", side_effect=HTTPError(response=Response()))
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
    device._connection._session_id = "test"
    device._connection.query.side_effect = [
        {
            "last_id": 3,
            "sectors": {
                0: {"id": 1, "index": 0, "element": 1, "activable": True, "status": True, "name": "S1 Living Room"},
                1: {"id": 2, "index": 1, "element": 2, "activable": True, "status": True, "name": "S2 Bedroom"},
                2: {"id": 3, "index": 2, "element": 3, "activable": False, "status": False, "name": "S3 Outdoor"},
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
        {
            "last_id": 3,
            "outputs": {
                0: {
                    "id": 1,
                    "index": 0,
                    "element": 1,
                    "control_denied_to_users": False,
                    "do_not_require_authentication": True,
                    "status": True,
                    "name": "Output 1",
                },
                1: {
                    "id": 2,
                    "index": 1,
                    "element": 2,
                    "control_denied_to_users": False,
                    "do_not_require_authentication": False,
                    "status": True,
                    "name": "Output 2",
                },
                2: {
                    "id": 3,
                    "index": 2,
                    "element": 3,
                    "control_denied_to_users": True,
                    "do_not_require_authentication": False,
                    "status": False,
                    "name": "Output 3",
                },
            },
        },
        {
            "last_id": 3,
            "alerts": {
                "alarm_led": 0,
                "anomalies_led": 1,
                "device_failure": 0,
                "device_low_battery": 0,
                "device_no_power": 0,
                "device_no_supervision": 0,
                "device_system_block": 0,
                "device_tamper": 0,
                "gsm_anomaly": 0,
                "gsm_low_balance": 0,
                "has_anomaly": False,
                "input_alarm": 0,
                "input_bypass": 0,
                "input_failure": 0,
                "input_low_battery": 0,
                "input_no_supervision": 0,
                "inputs_led": 2,
                "module_registration": 0,
                "panel_low_battery": 0,
                "panel_no_power": 0,
                "panel_tamper": 0,
                "pstn_anomaly": 0,
                "rf_interference": 0,
                "system_test": 0,
                "tamper_led": 0,
            },
        },
        {
            "last_id": 0,
            "panel": {
                "additional_info_supported": 1,
                "areas": 4,
                "brand": 0,
                "build": 1,
                "connection_type": "EthernetWiFi",
                "description": "T-800 1.0.1",
                "device_class": 92,
                "inputs": 24,
                "is_fire_panel": False,
                "language": 0,
                "last_connection": "01/01/1984 13:27:28",
                "last_disconnection": "01/10/1984 13:27:18",
                "login_without_user_id": True,
                "major": 1,
                "minor": 0,
                "model": "T-800",
                "operators": 64,
                "outputs": 24,
                "revision": 1,
                "sectors_in_use": [
                    True,
                    True,
                    True,
                    True,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                ],
                "sectors_per_area": 4,
                "source_ip": "10.0.0.1",
                "total_sectors": 16,
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
    device._connection._session_id = "test"
    device._connection.query.side_effect = [
        {
            "last_id": 3,
            "sectors": {
                0: {"id": 1, "index": 0, "element": 1, "activable": True, "status": False, "name": "S1 Living Room"},
                1: {"id": 2, "index": 1, "element": 2, "activable": True, "status": False, "name": "S2 Bedroom"},
                2: {"id": 3, "index": 2, "element": 3, "activable": False, "status": False, "name": "S3 Outdoor"},
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
        {
            "last_id": 3,
            "outputs": {
                0: {
                    "id": 1,
                    "index": 0,
                    "element": 1,
                    "control_denied_to_users": False,
                    "do_not_require_authentication": True,
                    "status": True,
                    "name": "Output 1",
                },
                1: {
                    "id": 2,
                    "index": 1,
                    "element": 2,
                    "control_denied_to_users": False,
                    "do_not_require_authentication": False,
                    "status": True,
                    "name": "Output 2",
                },
                2: {
                    "id": 3,
                    "index": 2,
                    "element": 3,
                    "control_denied_to_users": True,
                    "do_not_require_authentication": False,
                    "status": False,
                    "name": "Output 3",
                },
            },
        },
        {
            "last_id": 3,
            "alerts": {
                "alarm_led": 0,
                "anomalies_led": 1,
                "device_failure": 0,
                "device_low_battery": 0,
                "device_no_power": 0,
                "device_no_supervision": 0,
                "device_system_block": 0,
                "device_tamper": 0,
                "gsm_anomaly": 0,
                "gsm_low_balance": 0,
                "has_anomaly": False,
                "input_alarm": 0,
                "input_bypass": 0,
                "input_failure": 0,
                "input_low_battery": 0,
                "input_no_supervision": 0,
                "inputs_led": 2,
                "module_registration": 0,
                "panel_low_battery": 0,
                "panel_no_power": 0,
                "panel_tamper": 0,
                "pstn_anomaly": 0,
                "rf_interference": 0,
                "system_test": 0,
                "tamper_led": 0,
            },
        },
        {
            "last_id": 0,
            "panel": {
                "additional_info_supported": 1,
                "areas": 4,
                "brand": 0,
                "build": 1,
                "connection_type": "EthernetWiFi",
                "description": "T-800 1.0.1",
                "device_class": 92,
                "inputs": 24,
                "is_fire_panel": False,
                "language": 0,
                "last_connection": "01/01/1984 13:27:28",
                "last_disconnection": "01/10/1984 13:27:18",
                "login_without_user_id": True,
                "major": 1,
                "minor": 0,
                "model": "T-800",
                "operators": 64,
                "outputs": 24,
                "revision": 1,
                "sectors_in_use": [
                    True,
                    True,
                    True,
                    True,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                ],
                "sectors_per_area": 4,
                "source_ip": "10.0.0.1",
                "total_sectors": 16,
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


def test_device_register_sector(alarm_device, config_entry, coordinator):
    # Ensure a sector can register itself so the device can map entity ids to sector codes
    sector = SectorBinarySensor("test_id", 0, config_entry, "S1 Living Room", coordinator, alarm_device)
    alarm_device._register_sector(sector)
    assert alarm_device._sectors["econnect_metronet_test_user_s1_living_room"] == 1


def test_device_arm_success(alarm_device, mocker):
    """Should arm the e-connect system using the underlying client."""
    mocker.spy(alarm_device._connection, "lock")
    mocker.spy(alarm_device._connection, "arm")
    # Test
    alarm_device.arm("1234", sectors=[4])
    assert alarm_device._connection.lock.call_count == 1
    assert alarm_device._connection.arm.call_count == 1
    assert "1234" in alarm_device._connection.lock.call_args[0]
    assert {"sectors": [4]} == alarm_device._connection.arm.call_args[1]


def test_device_arm_success_without_panel_details(alarm_device, mocker):
    """Should assume `userId` is not required if panel details are empty."""
    alarm_device._inventory = {}
    mocker.spy(alarm_device._connection, "lock")
    mocker.spy(alarm_device._connection, "arm")
    # Test
    alarm_device._connection._session_id = "test"
    alarm_device.arm("1234", sectors=[4])
    assert alarm_device._connection.lock.call_count == 1
    assert alarm_device._connection.arm.call_count == 1
    assert "1234" in alarm_device._connection.lock.call_args[0]
    assert {"sectors": [4]} == alarm_device._connection.arm.call_args[1]


def test_device_arm_success_with_user_id(alarm_device, mocker):
    """Should split the code if the login with `userId` is required."""
    alarm_device._inventory[0]["login_without_user_id"] = False
    mocker.spy(alarm_device._connection, "lock")
    mocker.spy(alarm_device._connection, "arm")
    # Test
    alarm_device._connection._session_id = "test"
    alarm_device.arm("001123456", sectors=[4])
    assert alarm_device._connection.lock.call_count == 1
    assert alarm_device._connection.arm.call_count == 1
    assert "123456" in alarm_device._connection.lock.call_args[0]
    assert {"user_id": "001"} == alarm_device._connection.lock.call_args[1]
    assert {"sectors": [4]} == alarm_device._connection.arm.call_args[1]


def test_device_arm_success_user_id_not_required(alarm_device, mocker):
    """Should not split the code if the login with `userId` is not required."""
    alarm_device._inventory[0]["login_without_user_id"] = True
    mocker.spy(alarm_device._connection, "lock")
    mocker.spy(alarm_device._connection, "arm")
    # Test
    alarm_device._connection._session_id = "test"
    alarm_device.arm("123456", sectors=[4])
    assert alarm_device._connection.lock.call_count == 1
    assert alarm_device._connection.arm.call_count == 1
    assert "123456" in alarm_device._connection.lock.call_args[0]
    assert {"user_id": 1} == alarm_device._connection.lock.call_args[1]
    assert {"sectors": [4]} == alarm_device._connection.arm.call_args[1]


def test_device_arm_code_error_with_user_id(alarm_device, mocker):
    """Should raise an error if the code can't be split in `userId` and `code`."""
    alarm_device._inventory[0]["login_without_user_id"] = False
    mocker.spy(alarm_device._connection, "lock")
    mocker.spy(alarm_device._connection, "arm")
    # Test
    alarm_device._connection._session_id = "test"
    with pytest.raises(CodeError):
        alarm_device.arm("1234", sectors=[4])


def test_device_arm_error(client, mocker):
    """Should handle (log) connection errors."""
    device = AlarmDevice(client)
    mocker.spy(device._connection, "lock")
    mocker.spy(device._connection, "arm")
    device._connection.lock.side_effect = HTTPError(response=Response())
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


def test_device_disarm_success(alarm_device, mocker):
    """Should disarm the e-connect system using the underlying client."""
    mocker.spy(alarm_device._connection, "lock")
    mocker.spy(alarm_device._connection, "disarm")
    # Test
    alarm_device._connection._session_id = "test"
    alarm_device.disarm("1234", sectors=[4])

    assert alarm_device._connection.lock.call_count == 1
    assert alarm_device._connection.disarm.call_count == 1
    assert "1234" in alarm_device._connection.lock.call_args[0]
    assert {"sectors": [4]} == alarm_device._connection.disarm.call_args[1]


def test_device_disarm_activated_sectors(alarm_device, mocker):
    """Should disarm sectors that are currently activated if no sectors are specified."""
    mocker.spy(alarm_device._connection, "lock")
    mocker.spy(alarm_device._connection, "disarm")
    # Test
    alarm_device._connection._session_id = "test"
    alarm_device.disarm("1234")

    assert alarm_device._connection.lock.call_count == 1
    assert alarm_device._connection.disarm.call_count == 1
    assert "1234" in alarm_device._connection.lock.call_args[0]
    assert {"sectors": [1, 2]} == alarm_device._connection.disarm.call_args[1]


def test_device_disarm_success_without_panel_details(alarm_device, mocker):
    """Should assume `userId` is not required if panel details are empty."""
    alarm_device._inventory = {}
    mocker.spy(alarm_device._connection, "lock")
    mocker.spy(alarm_device._connection, "disarm")
    # Test
    alarm_device._connection._session_id = "test"
    alarm_device.disarm("1234", sectors=[4])
    assert alarm_device._connection.lock.call_count == 1
    assert alarm_device._connection.disarm.call_count == 1
    assert "1234" in alarm_device._connection.lock.call_args[0]
    assert {"sectors": [4]} == alarm_device._connection.disarm.call_args[1]


def test_device_disarm_success_user_id_not_required(alarm_device, mocker):
    """Should not split the code if the login with `userId` is not required."""
    alarm_device._inventory[0]["login_without_user_id"] = True
    mocker.spy(alarm_device._connection, "lock")
    mocker.spy(alarm_device._connection, "disarm")
    # Test
    alarm_device._connection._session_id = "test"
    alarm_device.disarm("123456", sectors=[4])
    assert alarm_device._connection.lock.call_count == 1
    assert alarm_device._connection.disarm.call_count == 1
    assert "123456" in alarm_device._connection.lock.call_args[0]
    assert {"user_id": 1} == alarm_device._connection.lock.call_args[1]
    assert {"sectors": [4]} == alarm_device._connection.disarm.call_args[1]


def test_device_disarm_success_with_user_id(alarm_device, mocker):
    """Should split the code if the login with `userId` is required."""
    alarm_device._inventory[0]["login_without_user_id"] = False
    mocker.spy(alarm_device._connection, "lock")
    mocker.spy(alarm_device._connection, "disarm")
    # Test
    alarm_device._connection._session_id = "test"
    alarm_device.disarm("001123456", sectors=[4])
    assert alarm_device._connection.lock.call_count == 1
    assert alarm_device._connection.disarm.call_count == 1
    assert "123456" in alarm_device._connection.lock.call_args[0]
    assert {"user_id": "001"} == alarm_device._connection.lock.call_args[1]
    assert {"sectors": [4]} == alarm_device._connection.disarm.call_args[1]


def test_device_disarm_code_error_with_user_id(alarm_device, mocker):
    """Should raise an error if the code can't be split in `userId` and `code`."""
    alarm_device._inventory[0]["login_without_user_id"] = False
    mocker.spy(alarm_device._connection, "lock")
    mocker.spy(alarm_device._connection, "disarm")
    # Test
    alarm_device._connection._session_id = "test"
    with pytest.raises(CodeError):
        alarm_device.disarm("1234", sectors=[4])


def test_device_disarm_error(client, mocker):
    """Should handle (log) connection errors."""
    device = AlarmDevice(client)
    mocker.spy(device._connection, "lock")
    mocker.spy(device._connection, "disarm")
    device._connection.lock.side_effect = HTTPError(response=Response())
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


def test_get_state_no_sectors_armed(alarm_device):
    """Test when no sectors are armed."""
    alarm_device._sectors_home = []
    alarm_device._sectors_night = []
    alarm_device._inventory = {9: {}}
    # Test
    assert alarm_device.get_state() == AlarmControlPanelState.DISARMED


def test_get_state_armed_home(alarm_device):
    """Test when sectors are armed for home."""
    alarm_device._sectors_home = [1, 2, 3]
    alarm_device._inventory = {
        9: {
            0: {"id": 1, "index": 0, "element": 1, "excluded": False, "status": True, "name": "S1 Living Room"},
            1: {"id": 2, "index": 1, "element": 2, "excluded": False, "status": True, "name": "S2 Bedroom"},
            2: {"id": 3, "index": 2, "element": 3, "excluded": False, "status": True, "name": "S3 Outdoor"},
        }
    }
    # Test
    assert alarm_device.get_state() == AlarmControlPanelState.ARMED_HOME


def test_get_state_armed_home_out_of_order(alarm_device):
    """Test when sectors are armed for home (out of order)."""
    alarm_device._sectors_home = [2, 1, 3]
    alarm_device._inventory = {
        9: {
            0: {"id": 1, "index": 0, "element": 3, "excluded": False, "status": True, "name": "S1 Living Room"},
            1: {"id": 2, "index": 1, "element": 1, "excluded": False, "status": True, "name": "S2 Bedroom"},
            2: {"id": 3, "index": 2, "element": 2, "excluded": False, "status": True, "name": "S3 Outdoor"},
        }
    }
    # Test
    assert alarm_device.get_state() == AlarmControlPanelState.ARMED_HOME


def test_get_state_armed_night(alarm_device):
    """Test when sectors are armed for night."""
    alarm_device._sectors_night = [4, 5, 6]
    alarm_device._inventory = {
        9: {
            0: {"id": 1, "index": 0, "element": 4, "excluded": False, "status": True, "name": "S1 Living Room"},
            1: {"id": 2, "index": 1, "element": 5, "excluded": False, "status": True, "name": "S2 Bedroom"},
            2: {"id": 3, "index": 2, "element": 6, "excluded": False, "status": True, "name": "S3 Outdoor"},
        }
    }
    # Test (out of order keys to test sorting)
    assert alarm_device.get_state() == AlarmControlPanelState.ARMED_NIGHT


def test_get_state_armed_night_out_of_order(alarm_device):
    """Test when sectors are armed for night (out of order)."""
    alarm_device._sectors_night = [5, 6, 4]
    alarm_device._inventory = {
        9: {
            0: {"id": 1, "index": 0, "element": 6, "excluded": False, "status": True, "name": "S1 Living Room"},
            1: {"id": 2, "index": 1, "element": 4, "excluded": False, "status": True, "name": "S2 Bedroom"},
            2: {"id": 3, "index": 2, "element": 5, "excluded": False, "status": True, "name": "S3 Outdoor"},
        }
    }
    # Test
    assert alarm_device.get_state() == AlarmControlPanelState.ARMED_NIGHT


def test_get_state_armed_vacation(alarm_device):
    """Test when sectors are armed for vacation."""
    alarm_device._sectors_vacation = [4, 5, 6]
    alarm_device._inventory = {
        9: {
            0: {"id": 1, "index": 0, "element": 4, "excluded": False, "status": True, "name": "S1 Living Room"},
            1: {"id": 2, "index": 1, "element": 5, "excluded": False, "status": True, "name": "S2 Bedroom"},
            2: {"id": 3, "index": 2, "element": 6, "excluded": False, "status": True, "name": "S3 Outdoor"},
        }
    }
    # Test (out of order keys to test sorting)
    assert alarm_device.get_state() == AlarmControlPanelState.ARMED_VACATION


def test_get_state_armed_vacation_out_of_order(alarm_device):
    """Test when sectors are armed for vacation (out of order)."""
    alarm_device._sectors_vacation = [5, 6, 4]
    alarm_device._inventory = {
        9: {
            0: {"id": 1, "index": 0, "element": 6, "excluded": False, "status": True, "name": "S1 Living Room"},
            1: {"id": 2, "index": 1, "element": 4, "excluded": False, "status": True, "name": "S2 Bedroom"},
            2: {"id": 3, "index": 2, "element": 5, "excluded": False, "status": True, "name": "S3 Outdoor"},
        }
    }
    # Test
    assert alarm_device.get_state() == AlarmControlPanelState.ARMED_VACATION


def test_get_state_armed_away(alarm_device):
    """Test when sectors are armed but don't match home or night."""
    alarm_device._sectors_away = []
    alarm_device._sectors_home = [1, 2, 3]
    alarm_device._sectors_night = [4, 5, 6]
    alarm_device._sectors_vacation = [4, 2]
    alarm_device._inventory = {
        9: {
            0: {"id": 1, "index": 0, "element": 1, "excluded": False, "status": True, "name": "S1 Living Room"},
            1: {"id": 2, "index": 1, "element": 2, "excluded": False, "status": True, "name": "S2 Bedroom"},
            2: {"id": 3, "index": 2, "element": 4, "excluded": False, "status": True, "name": "S3 Outdoor"},
        }
    }
    # Test
    assert alarm_device.get_state() == AlarmControlPanelState.ARMED_AWAY


def test_get_state_armed_mixed(alarm_device):
    """Test when some sectors from home and night are armed."""
    alarm_device._sectors_away = []
    alarm_device._sectors_home = [1, 2, 3]
    alarm_device._sectors_night = [4, 5, 6]
    alarm_device._inventory = {
        9: {
            0: {"id": 1, "index": 0, "element": 1, "excluded": False, "status": True, "name": "S1 Living Room"},
            1: {"id": 2, "index": 1, "element": 2, "excluded": False, "status": True, "name": "S2 Bedroom"},
            2: {"id": 3, "index": 2, "element": 3, "excluded": False, "status": True, "name": "S3 Outdoor"},
            3: {"id": 4, "index": 3, "element": 5, "excluded": False, "status": True, "name": "S5 Perimeter"},
        }
    }
    # Test
    assert alarm_device.get_state() == AlarmControlPanelState.ARMED_AWAY


def test_get_state_armed_away_with_config(alarm_device):
    # Ensure arm AWAY is set when it matches the config value
    alarm_device._sectors_away = [4]
    alarm_device._sectors_home = [1, 2, 3]
    alarm_device._sectors_night = [4, 5, 6]
    alarm_device._sectors_vacation = [4, 2]
    alarm_device._inventory = {
        9: {
            0: {"id": 1, "index": 0, "element": 1, "excluded": False, "status": False, "name": "S1 Living Room"},
            1: {"id": 2, "index": 1, "element": 2, "excluded": False, "status": False, "name": "S2 Bedroom"},
            2: {"id": 3, "index": 2, "element": 4, "excluded": False, "status": True, "name": "S3 Outdoor"},
        }
    }
    # Test
    assert alarm_device.get_state() == AlarmControlPanelState.ARMED_AWAY


def test_get_state_while_disarming(alarm_device):
    # Ensure that the state is not changed while disarming
    # Regression test for: https://github.com/palazzem/ha-econnect-alarm/issues/154
    alarm_device._sectors_home = []
    alarm_device._sectors_night = []
    alarm_device._inventory = {9: {}}
    alarm_device.state = AlarmControlPanelState.DISARMING
    # Test
    assert alarm_device.get_state() == AlarmControlPanelState.DISARMING


def test_get_state_while_arming(alarm_device):
    # Ensure that the state is not changed while arming
    # Regression test for: https://github.com/palazzem/ha-econnect-alarm/issues/154
    alarm_device._sectors_home = []
    alarm_device._sectors_night = []
    alarm_device._inventory = {9: {}}
    alarm_device.state = AlarmControlPanelState.ARMING
    # Test
    assert alarm_device.get_state() == AlarmControlPanelState.ARMING


class TestTurnOff:
    def test_required_authentication(self, alarm_device, mocker, caplog):
        # Ensure that API calls are not made when the output requires authentication
        mocker.spy(alarm_device._connection, "turn_off")
        alarm_device.turn_off(1)
        # Test
        assert "Device | Error while turning off output: Output 2, Required authentication" in caplog.text
        assert alarm_device._connection.turn_off.call_count == 0

    def test_no_manual_control(self, alarm_device, mocker, caplog):
        # Ensure that API calls are not made when the output cannot be manually controlled
        mocker.spy(alarm_device._connection, "turn_off")
        alarm_device.turn_off(2)
        # Test
        assert "Device | Error while turning off output: Output 3, Can't be manual controlled" in caplog.text
        assert alarm_device._connection.turn_off.call_count == 0

    def test_invalid_output(self, alarm_device, mocker, caplog):
        # Ensure that API calls are not made when the output is not valid
        mocker.spy(alarm_device._connection, "turn_off")
        alarm_device.turn_off(10)
        # Test
        assert alarm_device._connection.turn_off.call_count == 0

    def test_correct_output(self, alarm_device, mocker):
        # Ensure that API calls are made correctly
        mocker.spy(alarm_device._connection, "turn_off")
        alarm_device.turn_off(0)
        # Test
        assert alarm_device._connection.turn_off.call_count == 1
        assert (1) in alarm_device._connection.turn_off.call_args[0]

    def test_http_error(self, alarm_device, mocker):
        # Ensure if device's turn_off method raises HTTPError
        mocker.spy(alarm_device._connection, "turn_off")
        alarm_device._connection.turn_off.side_effect = HTTPError(response=Response())
        # Test
        with pytest.raises(HTTPError):
            alarm_device.turn_off(0)


class TestTurnOn:
    def test_required_authentication(self, alarm_device, mocker, caplog):
        # Ensure that API calls are not made when the output requires authentication
        mocker.spy(alarm_device._connection, "turn_on")
        alarm_device.turn_on(1)
        # Test
        assert "Device | Error while turning on output: Output 2, Required authentication" in caplog.text
        assert alarm_device._connection.turn_on.call_count == 0

    def test_no_manual_control(self, alarm_device, mocker, caplog):
        # Ensure that API calls are not made when the output cannot be manually controlled
        mocker.spy(alarm_device._connection, "turn_on")
        alarm_device.turn_on(2)
        # Test
        assert "Device | Error while turning on output: Output 3, Can't be manual controlled" in caplog.text
        assert alarm_device._connection.turn_on.call_count == 0

    def test_invalid_output(self, alarm_device, mocker, caplog):
        # Ensure that API calls are not made when the output is not valid
        mocker.spy(alarm_device._connection, "turn_on")
        alarm_device.turn_on(10)
        # Test
        assert alarm_device._connection.turn_on.call_count == 0

    def test_correct_output(self, alarm_device, mocker):
        # Ensure that API calls are made correctly
        mocker.spy(alarm_device._connection, "turn_on")
        alarm_device.turn_on(0)
        # Test
        assert alarm_device._connection.turn_on.call_count == 1
        assert (1) in alarm_device._connection.turn_on.call_args[0]

    def test_http_error(self, alarm_device, mocker):
        # Ensure if device's turn_on method raises HTTPError
        mocker.spy(alarm_device._connection, "turn_on")
        alarm_device._connection.turn_on.side_effect = HTTPError(response=Response())
        # Test
        with pytest.raises(HTTPError):
            alarm_device.turn_on(0)
