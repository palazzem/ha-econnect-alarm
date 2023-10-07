import logging

from elmo import query
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.econnect_metronet.binary_sensor import (
    AlertSensor,
    InputSensor,
    SectorSensor,
)


class TestAlertSensor:
    def test_binary_sensor_name(hass, config_entry, alarm_entity):
        # Ensure the alert has the right translation key
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = AlertSensor("test_id", "has_anomalies", config_entry, coordinator, alarm_entity)
        assert entity.translation_key == "has_anomalies"

    def test_binary_sensor_name_with_system_name(hass, config_entry, alarm_entity):
        # The system name doesn't change the translation key
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = AlertSensor("test_id", "has_anomalies", config_entry, coordinator, alarm_entity)
        assert entity.translation_key == "has_anomalies"

    def test_binary_sensor_entity_id(hass, config_entry, alarm_entity):
        # Ensure the alert has a valid Entity ID
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = AlertSensor("test_id", "has_anomalies", config_entry, coordinator, alarm_entity)
        assert entity.entity_id == "econnect_metronet.econnect_metronet_test_user_has_anomalies"

    def test_binary_sensor_entity_id_with_system_name(hass, config_entry, alarm_entity):
        # Ensure the Entity ID takes into consideration the system name
        config_entry.data["system_name"] = "Home"
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = AlertSensor("test_id", "has_anomalies", config_entry, coordinator, alarm_entity)
        assert entity.entity_id == "econnect_metronet.econnect_metronet_home_has_anomalies"


class TestInputSensor:
    def test_binary_sensor_name(hass, config_entry, alarm_entity):
        # Ensure the sensor has the right name
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = InputSensor("test_id", 1, config_entry, "1 Tamper Sirena", coordinator, alarm_entity, query.INPUTS)
        assert entity.name == "1 Tamper Sirena"

    def test_binary_sensor_name_with_system_name(hass, config_entry, alarm_entity):
        # The system name doesn't change the Entity name
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = InputSensor("test_id", 1, config_entry, "1 Tamper Sirena", coordinator, alarm_entity, query.INPUTS)
        assert entity.name == "1 Tamper Sirena"

    def test_binary_sensor_entity_id(hass, config_entry, alarm_entity):
        # Ensure the sensor has a valid Entity ID
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = InputSensor("test_id", 1, config_entry, "1 Tamper Sirena", coordinator, alarm_entity, query.INPUTS)
        assert entity.entity_id == "econnect_metronet.econnect_metronet_test_user_1_tamper_sirena"

    def test_binary_sensor_entity_id_with_system_name(hass, config_entry, alarm_entity):
        # Ensure the Entity ID takes into consideration the system name
        config_entry.data["system_name"] = "Home"
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = InputSensor("test_id", 1, config_entry, "1 Tamper Sirena", coordinator, alarm_entity, query.INPUTS)
        assert entity.entity_id == "econnect_metronet.econnect_metronet_home_1_tamper_sirena"


class TestSectorSensor:
    def test_binary_sensor_input_name(hass, config_entry, alarm_entity):
        # Ensure the sensor has the right name
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = SectorSensor("test_id", 1, config_entry, "1 S1 Living Room", coordinator, alarm_entity, query.INPUTS)
        assert entity.name == "1 S1 Living Room"

    def test_binary_sensor_input_name_with_system_name(hass, config_entry, alarm_entity):
        # The system name doesn't change the Entity name
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = SectorSensor("test_id", 1, config_entry, "1 S1 Living Room", coordinator, alarm_entity, query.INPUTS)
        assert entity.name == "1 S1 Living Room"

    def test_binary_sensor_input_entity_id(hass, config_entry, alarm_entity):
        # Ensure the sensor has a valid Entity ID
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = SectorSensor("test_id", 1, config_entry, "1 S1 Living Room", coordinator, alarm_entity, query.INPUTS)
        assert entity.entity_id == "econnect_metronet.econnect_metronet_test_user_1_s1_living_room"

    def test_binary_sensor_input_entity_id_with_system_name(hass, config_entry, alarm_entity):
        # Ensure the Entity ID takes into consideration the system name
        config_entry.data["system_name"] = "Home"
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = SectorSensor("test_id", 1, config_entry, "1 S1 Living Room", coordinator, alarm_entity, query.INPUTS)
        assert entity.entity_id == "econnect_metronet.econnect_metronet_home_1_s1_living_room"
