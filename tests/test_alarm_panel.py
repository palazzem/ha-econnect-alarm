import logging

import pytest
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.econnect_metronet.alarm_control_panel import EconnectAlarm
from custom_components.econnect_metronet.devices import AlarmDevice


def test_alarm_panel_name(client, hass, config_entry):
    # Ensure the Alarm Panel has the right name
    device = AlarmDevice(client)
    coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
    entity = EconnectAlarm("test_id", config_entry, device, coordinator)
    assert entity.name == "Alarm Panel test_user"


def test_alarm_panel_name_with_system_name(client, hass, config_entry):
    # Ensure the Entity ID takes into consideration the system optional name
    config_entry.data["system_name"] = "Home"
    device = AlarmDevice(client)
    coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
    entity = EconnectAlarm("test_id", config_entry, device, coordinator)
    assert entity.name == "Alarm Panel Home"


def test_alarm_panel_entity_id(client, hass, config_entry):
    # Ensure the Alarm Panel has a valid Entity ID
    device = AlarmDevice(client)
    coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
    entity = EconnectAlarm("test_id", config_entry, device, coordinator)
    assert entity.entity_id == "econnect_metronet.econnect_metronet_test_user"


def test_alarm_panel_entity_id_with_system_name(client, hass, config_entry):
    # Ensure the Entity ID takes into consideration the system name
    config_entry.data["system_name"] = "Home"
    device = AlarmDevice(client)
    coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
    entity = EconnectAlarm("test_id", config_entry, device, coordinator)
    assert entity.entity_id == "econnect_metronet.econnect_metronet_home"


@pytest.mark.asyncio
async def test_alarm_panel_arm_away(mocker, panel):
    # Ensure an empty AWAY config arms all sectors
    arm = mocker.patch.object(panel._device._connection, "arm", autopsec=True)
    # Test
    await panel.async_alarm_arm_away(code=42)
    assert arm.call_count == 1
    assert arm.call_args.kwargs["sectors"] == []


@pytest.mark.asyncio
async def test_alarm_panel_arm_away_with_options(mocker, panel):
    # Ensure an empty AWAY config arms all sectors
    arm = mocker.patch.object(panel._device._connection, "arm", autopsec=True)
    panel._device._sectors_away = [1, 2]
    # Test
    await panel.async_alarm_arm_away(code=42)
    assert arm.call_count == 1
    assert arm.call_args.kwargs["sectors"] == [1, 2]
