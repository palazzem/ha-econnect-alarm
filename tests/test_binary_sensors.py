import logging

from elmo import query
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.elmo_iess_alarm.binary_sensor import EconnectDoorWindowSensor


def test_binary_sensor_door_window_name(hass, config_entry, alarm_entity):
    # Ensure the Alarm Panel has the right name
    coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="elmo_iess_alarm")
    entity = EconnectDoorWindowSensor(
        "test_id", 1, config_entry, "1 Tamper Sirena", coordinator, alarm_entity, query.INPUTS
    )
    assert entity.name == "1 Tamper Sirena"


def test_binary_sensor_door_window_name_with_system_name(hass, config_entry, alarm_entity):
    # The system name doesn't change the Entity name
    coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="elmo_iess_alarm")
    entity = EconnectDoorWindowSensor(
        "test_id", 1, config_entry, "1 Tamper Sirena", coordinator, alarm_entity, query.INPUTS
    )
    assert entity.name == "1 Tamper Sirena"


def test_binary_sensor_door_window_entity_id(hass, config_entry, alarm_entity):
    # Ensure the Alarm Panel has a valid Entity ID
    coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="elmo_iess_alarm")
    entity = EconnectDoorWindowSensor(
        "test_id", 1, config_entry, "1 Tamper Sirena", coordinator, alarm_entity, query.INPUTS
    )
    assert entity.entity_id == "elmo_iess_alarm.elmo_iess_alarm_test_user_1_tamper_sirena"


def test_binary_sensor_door_window_entity_id_with_system_name(hass, config_entry, alarm_entity):
    # Ensure the Entity ID takes into consideration the system name
    config_entry.data["system_name"] = "Home"
    coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="elmo_iess_alarm")
    entity = EconnectDoorWindowSensor(
        "test_id", 1, config_entry, "1 Tamper Sirena", coordinator, alarm_entity, query.INPUTS
    )
    assert entity.entity_id == "elmo_iess_alarm.elmo_iess_alarm_home_1_tamper_sirena"
