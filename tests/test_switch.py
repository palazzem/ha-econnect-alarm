import logging

import pytest
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.econnect_metronet.const import DOMAIN
from custom_components.econnect_metronet.switch import OutputSwitch, async_setup_entry


@pytest.mark.asyncio
async def test_async_setup_entry_in_use(hass, config_entry, alarm_device, coordinator):
    # Ensure the async setup loads only outputs that are in use
    hass.data[DOMAIN][config_entry.entry_id] = {
        "device": alarm_device,
        "coordinator": coordinator,
    }

    # Test
    def ensure_only_in_use(outputs):
        assert len(outputs) == 3

    await async_setup_entry(hass, config_entry, ensure_only_in_use)


@pytest.mark.asyncio
async def test_async_setup_entry_unused_output(hass, config_entry, alarm_device, coordinator):
    # Ensure the async setup don't load outputs that are not in use
    hass.data[DOMAIN][config_entry.entry_id] = {
        "device": alarm_device,
        "coordinator": coordinator,
    }

    # Test
    def ensure_unused_output(outputs):
        for output in outputs:
            assert output._name not in ["Output 4"]

    await async_setup_entry(hass, config_entry, ensure_unused_output)


@pytest.mark.asyncio
async def test_async_setup_entry_outputs_unique_id(hass, config_entry, alarm_device, coordinator):
    # Ensure the async setup load correct unique_id for outputs
    hass.data[DOMAIN][config_entry.entry_id] = {
        "device": alarm_device,
        "coordinator": coordinator,
    }

    # Test
    def ensure_unique_id(outputs):
        assert outputs[2].unique_id == "test_entry_id_econnect_metronet_12_2"

    await async_setup_entry(hass, config_entry, ensure_unique_id)


class TestOutputSwitch:
    def test_switch_name(self, hass, config_entry, alarm_device):
        # Ensure the switch has the right name
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = OutputSwitch("test_id", 1, config_entry, "Output 2", coordinator, alarm_device)
        assert entity.name == "Output 2"

    def test_switch_name_with_system_name(self, hass, config_entry, alarm_device):
        # The system name doesn't change the Entity name
        config_entry.data["system_name"] = "Home"
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = OutputSwitch("test_id", 1, config_entry, "Output 2", coordinator, alarm_device)
        assert entity.name == "Output 2"

    def test_switch_entity_id(self, hass, config_entry, alarm_device):
        # Ensure the switch has a valid Entity ID
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = OutputSwitch("test_id", 1, config_entry, "Output 2", coordinator, alarm_device)
        assert entity.entity_id == "econnect_metronet.econnect_metronet_test_user_output_2"

    def test_switch_entity_id_with_system_name(self, hass, config_entry, alarm_device):
        # Ensure the Entity ID takes into consideration the system name
        config_entry.data["system_name"] = "Home"
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = OutputSwitch("test_id", 1, config_entry, "Output 2", coordinator, alarm_device)
        assert entity.entity_id == "econnect_metronet.econnect_metronet_home_output_2"

    def test_switch_unique_id(self, hass, config_entry, alarm_device):
        # Ensure the switch has the right unique ID
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = OutputSwitch("test_id", 1, config_entry, "Output 2", coordinator, alarm_device)
        assert entity.unique_id == "test_id"

    def test_switch_icon(self, hass, config_entry, alarm_device):
        # Ensure the switch has the right icon
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = OutputSwitch("test_id", 1, config_entry, "Output 2", coordinator, alarm_device)
        assert entity.icon == "hass:toggle-switch-variant"

    def test_switch_is_off(self, hass, config_entry, alarm_device):
        # Ensure the switch attribute is_on has the right status False
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = OutputSwitch("test_id", 2, config_entry, "Output 3", coordinator, alarm_device)
        assert entity.is_on is False

    def test_switch_is_on(self, hass, config_entry, alarm_device):
        # Ensure the switch attribute is_on has the right status True
        coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
        entity = OutputSwitch("test_id", 1, config_entry, "Output 1", coordinator, alarm_device)
        assert entity.is_on is True
