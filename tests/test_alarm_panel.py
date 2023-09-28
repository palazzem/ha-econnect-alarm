import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.elmo_iess_alarm.alarm_control_panel import EconnectAlarm
from custom_components.elmo_iess_alarm.devices import AlarmDevice


def test_alarm_panel_name(client, hass, config_entry):
    # Ensure the Alarm Panel has the right name
    device = AlarmDevice(client)
    coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="elmo_iess_alarm")
    entity = EconnectAlarm("test_id", config_entry, device, coordinator)
    assert entity.name == "Alarm Panel test_user"


def test_alarm_panel_name_with_system_name(client, hass, config_entry):
    # Ensure the Entity ID takes into consideration the system optional name
    config_entry.data["system_name"] = "Home"
    device = AlarmDevice(client)
    coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="elmo_iess_alarm")
    entity = EconnectAlarm("test_id", config_entry, device, coordinator)
    assert entity.name == "Alarm Panel Home"


def test_alarm_panel_entity_id(client, hass, config_entry):
    # Ensure the Alarm Panel has a valid Entity ID
    device = AlarmDevice(client)
    coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="elmo_iess_alarm")
    entity = EconnectAlarm("test_id", config_entry, device, coordinator)
    assert entity.entity_id == "elmo_iess_alarm.elmo_iess_alarm_test_user"


def test_alarm_panel_entity_id_with_system_name(client, hass, config_entry):
    # Ensure the Entity ID takes into consideration the system name
    config_entry.data["system_name"] = "Home"
    device = AlarmDevice(client)
    coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="elmo_iess_alarm")
    entity = EconnectAlarm("test_id", config_entry, device, coordinator)
    assert entity.entity_id == "elmo_iess_alarm.elmo_iess_alarm_home"
