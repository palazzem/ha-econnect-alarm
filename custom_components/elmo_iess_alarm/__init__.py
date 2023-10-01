"""The E-connect Alarm integration."""
import asyncio
import logging
from datetime import timedelta

import async_timeout
from elmo.api.client import ElmoClient
from elmo.api.exceptions import InvalidToken
from elmo.systems import ELMO_E_CONNECT as E_CONNECT_DEFAULT
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_DOMAIN,
    CONF_SCAN_INTERVAL,
    CONF_SYSTEM_URL,
    DOMAIN,
    KEY_COORDINATOR,
    KEY_DEVICE,
    KEY_UNSUBSCRIBER,
    POLLING_TIMEOUT,
    SCAN_INTERVAL_DEFAULT,
)
from .devices import AlarmDevice

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["alarm_control_panel", "binary_sensor"]


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    """Config flow migrations."""
    _LOGGER.info(f"Migrating from version {config_entry.version}")

    if config_entry.version == 1:
        # Config initialization
        migrated_config = {**config_entry.data}
        # Migration
        migrated_config[CONF_SYSTEM_URL] = E_CONNECT_DEFAULT
        config_entry.version = 2
        hass.config_entries.async_update_entry(config_entry, data=migrated_config)

    _LOGGER.info(f"Migration to version {config_entry.version} successful")
    return True


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the E-connect Alarm component."""
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up E-connect Alarm from a config entry."""
    # Initialize the device with an API endpoint and a vendor.
    # Calling `device.connect` authenticates the device via an access token
    # and asks for the first update, hence why in `async_setup_entry` there is no need
    # to call `coordinator.async_refresh()`.
    client = ElmoClient(entry.data[CONF_SYSTEM_URL], entry.data[CONF_DOMAIN])
    device = AlarmDevice(client, entry.options)
    await hass.async_add_executor_job(device.connect, entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])

    # Execute device update in a thread pool
    await hass.async_add_executor_job(device.update)

    async def async_update_data():
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # TODO: detect what happens if the update fails; check the unhappy path
            # TODO: use homeassistant.helpers.update_coordinator.UpdateFailed to
            # detect when an update fails.
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(POLLING_TIMEOUT):
                # `client.poll` implements e-connect long-polling API. This
                # action blocks the thread for at most 15 seconds, or when
                # something changes in the backend. POLLING_TIMEOUT ensures
                # an upper bound regardless of the underlying implementation.
                status = await hass.async_add_executor_job(device.has_updates)
                if status["has_changes"]:
                    # State machine is in `device.state`
                    return await hass.async_add_executor_job(device.update)
        except InvalidToken:
            await hass.async_add_executor_job(device.connect, entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])
            _LOGGER.info("Token was invalid or expired, re-authentication executed.")

    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL_DEFAULT)
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="elmo_iess_alarm",
        update_interval=timedelta(seconds=scan_interval),
        update_method=async_update_data,
    )

    # Store an AlarmDevice instance to access the cloud service.
    # It includes a DataUpdateCoordinator shared across entities to get a full
    # status update with a single request.
    hass.data[DOMAIN][entry.entry_id] = {
        KEY_DEVICE: device,
        KEY_COORDINATOR: coordinator,
    }

    # Register a listener when option changes
    unsub = entry.add_update_listener(options_update_listener)
    hass.data[DOMAIN][entry.entry_id][KEY_UNSUBSCRIBER] = unsub

    for component in PLATFORMS:
        hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, component))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[hass.config_entries.async_forward_entry_unload(entry, component) for component in PLATFORMS]
        )
    )
    if unload_ok:
        # Call the options unsubscriber and remove the configuration
        hass.data[DOMAIN][entry.entry_id][KEY_UNSUBSCRIBER]()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
