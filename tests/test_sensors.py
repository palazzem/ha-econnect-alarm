import logging

import pytest
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.econnect_metronet.const import DOMAIN
from custom_components.econnect_metronet.sensor import AlertSensor, async_setup_entry


@pytest.mark.asyncio
async def test_async_setup_entry_only_sensors(hass, config_entry, alarm_device, coordinator):
    # Ensure the async setup loads only alert sensors
    hass.data[DOMAIN][config_entry.entry_id] = {
        "device": alarm_device,
        "coordinator": coordinator,
    }

    # Test
    def ensure_only_sensors(sensors):
        assert len(sensors) == 3

    await async_setup_entry(hass, config_entry, ensure_only_sensors)


@pytest.mark.asyncio
async def test_async_setup_entry_alerts_unique_id(hass, config_entry, alarm_device, coordinator):
    # Ensure that the alert sensors have the correct unique IDs
    hass.data[DOMAIN][config_entry.entry_id] = {
        "device": alarm_device,
        "coordinator": coordinator,
    }

    # Test
    def ensure_unique_id(sensors):
        assert sensors[1].unique_id == "test_entry_id_econnect_metronet_11_16"

    await async_setup_entry(hass, config_entry, ensure_unique_id)


class TestAlertSensor:
    def test_sensor_native_value(self, hass, config_entry, alarm_device):
        # Ensure the sensor attribute native_value has the right status
        coordinator = DataUpdateCoordinator(
            hass, logging.getLogger(__name__), config_entry=config_entry, name="econnect_metronet"
        )
        entity = AlertSensor("test_id", 16, config_entry, "input_led", coordinator, alarm_device)
        assert entity.native_value == 2

    def test_sensor_missing(self, hass, config_entry, alarm_device):
        # Ensure the sensor raise keyerror if the alert is missing
        coordinator = DataUpdateCoordinator(
            hass, logging.getLogger(__name__), config_entry=config_entry, name="econnect_metronet"
        )
        entity = AlertSensor("test_id", 1000, config_entry, "test_id", coordinator, alarm_device)
        with pytest.raises(KeyError):
            assert entity.native_value == 1

    def test_sensor_name(self, hass, config_entry, alarm_device):
        # Ensure the alert has the right translation key
        coordinator = DataUpdateCoordinator(
            hass, logging.getLogger(__name__), config_entry=config_entry, name="econnect_metronet"
        )
        entity = AlertSensor("test_id", 16, config_entry, "input_led", coordinator, alarm_device)
        assert entity.translation_key == "input_led"

    def test_binary_sensor_name_with_system_name(self, hass, config_entry, alarm_device):
        # The system name doesn't change the translation key
        hass.config_entries.async_update_entry(config_entry, data={"system_name": "Home"})
        coordinator = DataUpdateCoordinator(
            hass, logging.getLogger(__name__), config_entry=config_entry, name="econnect_metronet"
        )
        entity = AlertSensor("test_id", 0, config_entry, "input_led", coordinator, alarm_device)
        assert entity.translation_key == "input_led"

    def test_sensor_entity_id(self, hass, config_entry, alarm_device):
        # Ensure the alert has a valid Entity ID
        coordinator = DataUpdateCoordinator(
            hass, logging.getLogger(__name__), config_entry=config_entry, name="econnect_metronet"
        )
        entity = AlertSensor("test_id", 0, config_entry, "input_led", coordinator, alarm_device)
        assert entity.entity_id == "econnect_metronet.econnect_metronet_test_user_input_led"

    def test_sensor_entity_id_with_system_name(self, hass, config_entry, alarm_device):
        # Ensure the Entity ID takes into consideration the system name
        hass.config_entries.async_update_entry(config_entry, data={"system_name": "Home"})
        coordinator = DataUpdateCoordinator(
            hass, logging.getLogger(__name__), config_entry=config_entry, name="econnect_metronet"
        )
        entity = AlertSensor("test_id", 0, config_entry, "input_led", coordinator, alarm_device)
        assert entity.entity_id == "econnect_metronet.econnect_metronet_home_input_led"

    def test_sensor_unique_id(self, hass, config_entry, alarm_device):
        # Ensure the alert has the right unique ID
        coordinator = DataUpdateCoordinator(
            hass, logging.getLogger(__name__), config_entry=config_entry, name="econnect_metronet"
        )
        entity = AlertSensor("test_id", 0, config_entry, "input_led", coordinator, alarm_device)
        assert entity.unique_id == "test_id"

    def test_sensor_icon(self, hass, config_entry, alarm_device):
        # Ensure the sensor has the right icon
        coordinator = DataUpdateCoordinator(
            hass, logging.getLogger(__name__), config_entry=config_entry, name="econnect_metronet"
        )
        entity = AlertSensor("test_id", 0, config_entry, "input_led", coordinator, alarm_device)
        assert entity.icon == "hass:alarm-light"
