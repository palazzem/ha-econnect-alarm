from datetime import timedelta

import pytest
from elmo.api.exceptions import CredentialError, DeviceDisconnectedError, InvalidToken
from homeassistant.exceptions import ConfigEntryNotReady
from requests.exceptions import HTTPError

from custom_components.econnect_metronet.coordinator import AlarmCoordinator


def test_coordinator_constructor(hass, alarm_device):
    # Ensure that the coordinator is initialized correctly
    coordinator = AlarmCoordinator(hass, alarm_device, 42)
    assert coordinator.name == "econnect_metronet"
    assert coordinator.update_interval == timedelta(seconds=42)
    assert coordinator._device is alarm_device


@pytest.mark.asyncio
async def test_coordinator_async_update_no_data(mocker, coordinator):
    # Ensure that the coordinator returns an empty list if no changes are detected
    mocker.patch.object(coordinator._device, "has_updates")
    coordinator._device.has_updates.return_value = {"has_changes": False}
    # Test
    await coordinator.async_refresh()
    assert coordinator.data == {}


@pytest.mark.asyncio
async def test_coordinator_async_update_with_data(mocker, coordinator):
    # Ensure that the coordinator returns data when changes are detected
    mocker.patch.object(coordinator._device, "has_updates")
    coordinator._device.has_updates.return_value = {"has_changes": True}
    # Test
    await coordinator.async_refresh()
    assert coordinator.data == {
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
        10: {
            0: {"element": 1, "excluded": False, "id": 1, "index": 0, "name": "Entryway Sensor", "status": True},
            1: {"element": 2, "excluded": False, "id": 2, "index": 1, "name": "Outdoor Sensor 1", "status": True},
            2: {"element": 3, "excluded": True, "id": 3, "index": 2, "name": "Outdoor Sensor 2", "status": False},
        },
        9: {
            0: {"element": 1, "activable": True, "id": 1, "index": 0, "name": "S1 Living Room", "status": True},
            1: {"element": 2, "activable": True, "id": 2, "index": 1, "name": "S2 Bedroom", "status": True},
            2: {"element": 3, "activable": False, "id": 3, "index": 2, "name": "S3 Outdoor", "status": False},
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


@pytest.mark.asyncio
async def test_coordinator_async_update_invalid_token(mocker, coordinator):
    # Ensure a new connection is established when the token is invalid
    # No exceptions must be raised as this is a normal condition
    mocker.patch.object(coordinator._device, "has_updates")
    coordinator._device.has_updates.side_effect = InvalidToken()
    mocker.spy(coordinator._device, "connect")
    # Test
    await coordinator._async_update_data()
    coordinator._device.connect.assert_called_once_with("test_user", "test_password")


@pytest.mark.asyncio
async def test_coordinator_async_update_failed(mocker, coordinator):
    # Resetting the connection, forces an update during the next run. This is required to prevent
    # a misalignment between the `AlarmDevice` and backend known IDs, needed to implement
    # the long-polling strategy. If IDs are misaligned, then no updates happen and
    # the integration remains stuck.
    # Regression test for: https://github.com/palazzem/ha-econnect-alarm/issues/51
    coordinator.last_update_success = False
    mocker.spy(coordinator._device, "update")
    mocker.spy(coordinator._device, "has_updates")
    # Test
    await coordinator._async_update_data()
    assert coordinator._device.update.call_count == 1
    assert coordinator._device.has_updates.call_count == 0


@pytest.mark.asyncio
async def test_coordinator_first_refresh_auth(mocker, coordinator):
    # Ensure the first refresh authenticates before joining the scheduler
    coordinator.data = None
    mocker.spy(coordinator._device, "connect")
    # Test
    await coordinator.async_config_entry_first_refresh()
    coordinator._device.connect.assert_called_once_with("test_user", "test_password")


@pytest.mark.asyncio
async def test_coordinator_first_refresh_update(mocker, coordinator):
    # Ensure the first refresh updates before joining the scheduler
    # This is required to avoid registering entities without a proper state
    coordinator.data = None
    mocker.patch.object(coordinator._device, "has_updates")
    coordinator._device.has_updates.return_value = {"has_changes": False}
    mocker.spy(coordinator._device, "update")
    # Test
    await coordinator.async_config_entry_first_refresh()
    assert coordinator._device.update.call_count == 1


@pytest.mark.asyncio
async def test_coordinator_first_refresh_auth_failed(mocker, coordinator):
    # Ensure a configuration exception is raised if the first refresh fails
    coordinator.data = None
    mocker.patch.object(coordinator._device, "connect")
    coordinator._device.connect.side_effect = CredentialError()
    # Test
    with pytest.raises(ConfigEntryNotReady):
        await coordinator.async_config_entry_first_refresh()


@pytest.mark.asyncio
async def test_coordinator_first_refresh_update_failed(mocker, coordinator):
    # Ensure a configuration exception is raised if the first refresh fails
    coordinator.data = None
    mocker.patch.object(coordinator._device, "update")
    coordinator._device.update.side_effect = HTTPError()
    # Test
    with pytest.raises(ConfigEntryNotReady):
        await coordinator.async_config_entry_first_refresh()


@pytest.mark.asyncio
async def test_coordinator_poll_with_disconnected_device(mocker, coordinator):
    # Ensure the coordinator handles a disconnected device during polling
    # Regression test for: https://github.com/palazzem/ha-econnect-alarm/issues/148
    query = mocker.patch.object(coordinator._device._connection, "query")
    coordinator._device._connection.query.side_effect = DeviceDisconnectedError()
    # Test
    await coordinator._async_update_data()
    assert query.call_count == 1
    assert coordinator._device.connected is False


@pytest.mark.asyncio
async def test_coordinator_poll_recover_disconnected_device(coordinator):
    # Ensure the coordinator recovers the connection state from a previous disconnected device error
    coordinator._device.connected = False
    # Test
    await coordinator._async_update_data()
    assert coordinator._device.connected is True


@pytest.mark.asyncio
async def test_coordinator_update_with_disconnected_device(mocker, coordinator):
    # Ensure the coordinator handles a disconnected device during updates
    # Regression test for: https://github.com/palazzem/ha-econnect-alarm/issues/148
    mocker.patch.object(coordinator._device, "has_updates")
    mocker.patch.object(coordinator._device._connection, "query")
    update = mocker.spy(coordinator._device, "update")
    coordinator._device.has_updates.return_value = {"has_changes": True}
    coordinator._device._connection.query.side_effect = DeviceDisconnectedError()
    # Test
    await coordinator._async_update_data()
    assert update.call_count == 1
    assert coordinator._device.connected is False


@pytest.mark.asyncio
async def test_coordinator_update_recover_disconnected_device(mocker, coordinator):
    # Ensure the coordinator recovers the connection state from a previous disconnected device error
    mocker.patch.object(coordinator._device, "has_updates")
    coordinator._device.has_updates.return_value = {"has_changes": True}
    coordinator._device.connected = False
    # Test
    await coordinator._async_update_data()
    assert coordinator._device.connected is True


@pytest.mark.asyncio
async def test_coordinator_async_update_disconnected_device(mocker, coordinator):
    # Ensure a full update is forced if the device was previously disconnected
    # Regression test for: https://github.com/palazzem/ha-econnect-alarm/issues/148
    coordinator._device.connected = False
    mocker.spy(coordinator._device, "update")
    mocker.spy(coordinator._device, "has_updates")
    # Test
    await coordinator._async_update_data()
    assert coordinator._device.update.call_count == 1
    assert coordinator._device.has_updates.call_count == 0
