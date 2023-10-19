import logging

import pytest
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.econnect_metronet.binary_sensor import (
    AlertSensor,
    InputSensor,
    SectorSensor,
)


class TestAlertSensor:
    def test_binary_sensor_is_on(self, hass, config_entry, alarm_device):
        # Ensure the sensor attribute is_on has the right status True
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = AlertSensor("device_tamper", 7, config_entry, "device_tamper", coordinator, alarm_device)
        assert entity.is_on is True

    def test_binary_sensor_is_off(self, hass, config_entry, alarm_device):
        # Ensure the sensor attribute is_on has the right status False
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = AlertSensor("device_failure", 2, config_entry, "device_failure", coordinator, alarm_device)
        assert entity.is_on is False

    def test_binary_sensor_missing(self, hass, config_entry, alarm_device):
        # Ensure the sensor attribute is_on has the right status False if the alert is missing
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = AlertSensor("test_id", 1000, config_entry, "test_id", coordinator, alarm_device)
        with pytest.raises(KeyError):
            assert entity.is_on is False

    def test_binary_sensor_anomalies_led_is_off(self, hass, config_entry, alarm_device):
        # Ensure the sensor attribute is_on has the right status False
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = AlertSensor("anomalies_led", 1, config_entry, "anomalies_led", coordinator, alarm_device)
        assert entity.is_on is False

    def test_binary_sensor_anomalies_led_is_on(self, hass, config_entry, alarm_device):
        # Ensure the sensor attribute is_on has the right status True
        alarm_device._inventory[11][1]["status"] = 2
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = AlertSensor("anomalies_led", 1, config_entry, "anomalies_led", coordinator, alarm_device)
        assert entity.is_on is True

    def test_binary_sensor_name(self, hass, config_entry, alarm_device):
        # Ensure the alert has the right translation key
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = AlertSensor("test_id", 0, config_entry, "has_anomalies", coordinator, alarm_device)
        assert entity.translation_key == "has_anomalies"

    def test_binary_sensor_name_with_system_name(self, hass, config_entry, alarm_device):
        # The system name doesn't change the translation key
        config_entry.data["system_name"] = "Home"
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = AlertSensor("test_id", 0, config_entry, "has_anomalies", coordinator, alarm_device)
        assert entity.translation_key == "has_anomalies"

    def test_binary_sensor_entity_id(self, hass, config_entry, alarm_device):
        # Ensure the alert has a valid Entity ID
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = AlertSensor("test_id", 0, config_entry, "has_anomalies", coordinator, alarm_device)
        assert entity.entity_id == "econnect_metronet.econnect_metronet_test_user_has_anomalies"

    def test_binary_sensor_entity_id_with_system_name(self, hass, config_entry, alarm_device):
        # Ensure the Entity ID takes into consideration the system name
        config_entry.data["system_name"] = "Home"
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = AlertSensor("test_id", 0, config_entry, "has_anomalies", coordinator, alarm_device)
        assert entity.entity_id == "econnect_metronet.econnect_metronet_home_has_anomalies"

    def test_binary_sensor_icon(self, hass, config_entry, alarm_device):
        # Ensure the sensor has the right icon
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = AlertSensor("test_id", 0, config_entry, "has_anomalies", coordinator, alarm_device)
        assert entity.icon == "hass:alarm-light"


class TestInputSensor:
    def test_binary_sensor_name(self, hass, config_entry, alarm_device):
        # Ensure the sensor has the right name
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = InputSensor("test_id", 1, config_entry, "1 Tamper Sirena", coordinator, alarm_device)
        assert entity.name == "1 Tamper Sirena"

    def test_binary_sensor_name_with_system_name(self, hass, config_entry, alarm_device):
        # The system name doesn't change the Entity name
        config_entry.data["system_name"] = "Home"
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = InputSensor("test_id", 1, config_entry, "1 Tamper Sirena", coordinator, alarm_device)
        assert entity.name == "1 Tamper Sirena"

    def test_binary_sensor_entity_id(self, hass, config_entry, alarm_device):
        # Ensure the sensor has a valid Entity ID
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = InputSensor("test_id", 1, config_entry, "1 Tamper Sirena", coordinator, alarm_device)
        assert entity.entity_id == "econnect_metronet.econnect_metronet_test_user_1_tamper_sirena"

    def test_binary_sensor_entity_id_with_system_name(self, hass, config_entry, alarm_device):
        # Ensure the Entity ID takes into consideration the system name
        config_entry.data["system_name"] = "Home"
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = InputSensor("test_id", 1, config_entry, "1 Tamper Sirena", coordinator, alarm_device)
        assert entity.entity_id == "econnect_metronet.econnect_metronet_home_1_tamper_sirena"

    def test_binary_sensor_icon(self, hass, config_entry, alarm_device):
        # Ensure the sensor has the right icon
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = InputSensor("test_id", 1, config_entry, "1 Tamper Sirena", coordinator, alarm_device)
        assert entity.icon == "hass:electric-switch"

    def test_binary_sensor_off(self, hass, config_entry, alarm_device):
        # Ensure the sensor attribute is_on has the right status False
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = InputSensor("test_id", 2, config_entry, "Outdoor Sensor 2", coordinator, alarm_device)
        assert entity.is_on is False

    def test_binary_sensor_on(self, hass, config_entry, alarm_device):
        # Ensure the sensor attribute is_on has the right status True
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = InputSensor("test_id", 1, config_entry, "Outdoor Sensor 1", coordinator, alarm_device)
        assert entity.is_on is True


class TestSectorSensor:
    def test_binary_sensor_input_name(self, hass, config_entry, alarm_device):
        # Ensure the sensor has the right name
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = SectorSensor("test_id", 1, config_entry, "1 S1 Living Room", coordinator, alarm_device)
        assert entity.name == "1 S1 Living Room"

    def test_binary_sensor_input_name_with_system_name(self, hass, config_entry, alarm_device):
        # The system name doesn't change the Entity name
        config_entry.data["system_name"] = "Home"
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = SectorSensor("test_id", 1, config_entry, "1 S1 Living Room", coordinator, alarm_device)
        assert entity.name == "1 S1 Living Room"

    def test_binary_sensor_input_entity_id(self, hass, config_entry, alarm_device):
        # Ensure the sensor has a valid Entity ID
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = SectorSensor("test_id", 1, config_entry, "1 S1 Living Room", coordinator, alarm_device)
        assert entity.entity_id == "econnect_metronet.econnect_metronet_test_user_1_s1_living_room"

    def test_binary_sensor_input_entity_id_with_system_name(self, hass, config_entry, alarm_device):
        # Ensure the Entity ID takes into consideration the system name
        config_entry.data["system_name"] = "Home"
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = SectorSensor("test_id", 1, config_entry, "1 S1 Living Room", coordinator, alarm_device)
        assert entity.entity_id == "econnect_metronet.econnect_metronet_home_1_s1_living_room"

    def test_binary_sensor_icon(self, hass, config_entry, alarm_device):
        # Ensure the sensor has the right icon
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = SectorSensor("test_id", 1, config_entry, "1 Tamper Sirena", coordinator, alarm_device)
        assert entity.icon == "hass:shield-home-outline"

    def test_binary_sensor_off(self, hass, config_entry, alarm_device):
        # Ensure the sensor attribute is_on has the right status False
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = SectorSensor("test_id", 2, config_entry, "S3 Outdoor", coordinator, alarm_device)
        assert entity.is_on is False

    def test_binary_sensor_on(self, hass, config_entry, alarm_device):
        # Ensure the sensor attribute is_on has the right status True
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = SectorSensor("test_id", 1, config_entry, "1 Tamper Sirena", coordinator, alarm_device)
        alarm_device.sectors_armed.update({entity._sector_id: {}})
        assert entity.is_on is True
