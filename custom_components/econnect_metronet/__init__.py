"""The E-connect Alarm integration."""

import asyncio
import logging
from functools import partial

import voluptuous as vol
from elmo.api.client import ElmoClient
from elmo.systems import ELMO_E_CONNECT as E_CONNECT_DEFAULT
from homeassistant.config_entries import ConfigEntry, ConfigType
from homeassistant.core import HomeAssistant

from . import services
from .const import (
    CONF_DOMAIN,
    CONF_EXPERIMENTAL,
    CONF_SCAN_INTERVAL,
    CONF_SYSTEM_URL,
    DOMAIN,
    KEY_COORDINATOR,
    KEY_DEVICE,
    KEY_UNSUBSCRIBER,
    SCAN_INTERVAL_DEFAULT,
)
from .coordinator import AlarmCoordinator
from .devices import AlarmDevice

_LOGGER = logging.getLogger(__name__)

# Allow experimental settings to be exposed in the YAML configuration
# This part will be removed once the experimental settings are stable
# and moved to the configuration flow. This is considered an internal
# API so it will be removed without notice.
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional("experimental"): vol.Schema({}, extra=vol.ALLOW_EXTRA),
            }
        ),
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = ["alarm_control_panel", "binary_sensor", "sensor", "switch"]


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

    if config.version == 2:
        # Config initialization
        options = {**config.options}
        options_to_migrate = ["areas_arm_home", "areas_arm_night", "areas_arm_vacation"]
        migrated_options = {}
        # Migration
        config.version = 3
        for key, value in options.items():
            if key in options_to_migrate:
                migrated_options[key] = [int(area) for area in value.split(",")]
            else:
                migrated_options[key] = value
        hass.config_entries.async_update_entry(config, options=migrated_options)

    _LOGGER.info(f"Migration to version {config.version} successful")
    return True


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Initialize the E-connect Alarm integration.

    This method exposes eventual YAML configuration options under the DOMAIN key.
    Use YAML configurations only to expose experimental settings, otherwise use
    the configuration flow.
    """
    hass.data[DOMAIN] = config.get(DOMAIN, {})
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
    """
    # Enable experimental settings from the configuration file
    # NOTE: While it's discouraged to use YAML configurations for integrations, this approach
    # ensures that we can experiment with new settings we can break without notice.
    experimental = hass.data[DOMAIN].get(CONF_EXPERIMENTAL, {})

    # Initialize Components
    scan_interval = config.options.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL_DEFAULT)
    client = ElmoClient(config.data[CONF_SYSTEM_URL], config.data[CONF_DOMAIN])
    device = AlarmDevice(client, {**config.options, **experimental})
    coordinator = AlarmCoordinator(hass, device, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    # Store an AlarmDevice instance to access the cloud service.
    # It includes a DataUpdateCoordinator shared across entities to get a full
    # status update with a single request.
    hass.data[DOMAIN][config.entry_id] = {
        KEY_DEVICE: device,
        KEY_COORDINATOR: coordinator,
    }

    # Register a listener when option changes
    unsub = config.add_update_listener(options_update_listener)
    hass.data[DOMAIN][config.entry_id][KEY_UNSUBSCRIBER] = unsub

    # Register e-Connect services
    # We use a `partial` function to pass the `hass` and `config.entry_id` arguments
    # as we need both to access the integration configurations.
    hass.services.async_register(DOMAIN, "arm_sectors", partial(services.arm_sectors, hass, config.entry_id))
    hass.services.async_register(DOMAIN, "disarm_sectors", partial(services.disarm_sectors, hass, config.entry_id))

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
