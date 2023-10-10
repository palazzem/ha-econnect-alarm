"""The E-connect Alarm integration."""
import asyncio
import logging

from elmo.systems import ELMO_E_CONNECT as E_CONNECT_DEFAULT
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_SYSTEM_URL,
    DOMAIN,
    KEY_COORDINATOR,
    KEY_DEVICE,
    KEY_UNSUBSCRIBER,
)
from .coordinator import AlarmCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["alarm_control_panel", "binary_sensor"]


async def async_migrate_entry(hass, config: ConfigEntry):
    """Config flow migrations."""
    _LOGGER.info(f"Migrating from version {config.version}")

    if config.version == 1:
        # Config initialization
        migrated_config = {**config.data}
        # Migration
        migrated_config[CONF_SYSTEM_URL] = E_CONNECT_DEFAULT
        config.version = 2
        hass.config_entries.async_update_entry(config, data=migrated_config)

    _LOGGER.info(f"Migration to version {config.version} successful")
    return True


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the E-connect Alarm component."""
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry) -> bool:
    """Set up a configuration entry for the alarm device in Home Assistant.

    This asynchronous method initializes an AlarmDevice instance to access the cloud service.
    It uses a DataUpdateCoordinator to aggregate status updates from different entities
    into a single request. The method also registers a listener to track changes in the configuration options.

    Args:
        hass (HomeAssistant): The Home Assistant instance.
        config (ConfigEntry): The configuration entry containing the setup details for the alarm device.

    Returns:
        bool: True if the setup was successful, False otherwise.

    Raises:
        Any exceptions raised by the coordinator or the setup process will be propagated up to the caller.

    Notes:
        The function should be called as part of the Home Assistant setup process, typically
        during the initialization of a custom component.
    """

    coordinator = AlarmCoordinator(hass, config)
    await coordinator.async_config_entry_first_refresh()

    # Store an AlarmDevice instance to access the cloud service.
    # It includes a DataUpdateCoordinator shared across entities to get a full
    # status update with a single request.
    hass.data[DOMAIN][config.entry_id] = {
        KEY_DEVICE: coordinator.device,
        KEY_COORDINATOR: coordinator,
    }

    # Register a listener when option changes
    unsub = config.add_update_listener(options_update_listener)
    hass.data[DOMAIN][config.entry_id][KEY_UNSUBSCRIBER] = unsub

    for component in PLATFORMS:
        hass.async_create_task(hass.config_entries.async_forward_entry_setup(config, component))

    return True


async def async_unload_entry(hass: HomeAssistant, config: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[hass.config_entries.async_forward_entry_unload(config, component) for component in PLATFORMS]
        )
    )
    if unload_ok:
        # Call the options unsubscriber and remove the configuration
        hass.data[DOMAIN][config.entry_id][KEY_UNSUBSCRIBER]()
        hass.data[DOMAIN].pop(config.entry_id)

    return unload_ok


async def options_update_listener(hass: HomeAssistant, config: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(config.entry_id)
