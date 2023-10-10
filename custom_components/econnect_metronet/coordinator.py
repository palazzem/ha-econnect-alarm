import logging
from datetime import timedelta

import async_timeout
from elmo.api.client import ElmoClient
from elmo.api.exceptions import InvalidToken
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_DOMAIN,
    CONF_SCAN_INTERVAL,
    CONF_SYSTEM_URL,
    DOMAIN,
    POLLING_TIMEOUT,
    SCAN_INTERVAL_DEFAULT,
)
from .devices import AlarmDevice

_LOGGER = logging.getLogger(__name__)


class AlarmCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, config: ConfigEntry):
        # Initialize all clients and devices
        client = ElmoClient(config.data[CONF_SYSTEM_URL], config.data[CONF_DOMAIN])
        scan_interval = config.options.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL_DEFAULT)

        # Attributes
        self.device = AlarmDevice(client, config.options)

        # Configure the coordinator
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def async_config_entry_first_refresh(self) -> None:
        """Refresh data for the first time when a config entry is setup.

        Will automatically raise ConfigEntryNotReady if the refresh
        fails. Additionally logging is handled by config entry setup
        to ensure that multiple retries do not cause log spam.
        """
        _LOGGER.debug("Coordinator | First authentication")
        username = self.config_entry.data[CONF_USERNAME]
        password = self.config_entry.data[CONF_PASSWORD]
        await self.hass.async_add_executor_job(self.device.connect, username, password)
        _LOGGER.debug("Coordinator | Authentication successful")
        return await super().async_config_entry_first_refresh()

    async def _async_update_data(self):
        try:
            # `device.has_updates` implements e-Connect long-polling API. This
            # action blocks the thread for 15 seconds, or when the backend publishes an update
            # POLLING_TIMEOUT ensures an upper bound regardless of the underlying implementation.
            async with async_timeout.timeout(POLLING_TIMEOUT):
                status = await self.hass.async_add_executor_job(self.device.has_updates)
                if status["has_changes"]:
                    _LOGGER.debug("Coordinator | Changes detected, sending an update")
                    # State machine is in `device.state`
                    return await self.hass.async_add_executor_job(self.device.update)
                else:
                    _LOGGER.debug("Coordinator | No changes detected")
                    return None
        except InvalidToken:
            _LOGGER.debug("Coordinator | Invalid token detected, authenticating")
            username = self.config_entry.data[CONF_USERNAME]
            password = self.config_entry.data[CONF_PASSWORD]
            await self.hass.async_add_executor_job(self.device.connect, username, password)
            _LOGGER.debug("Coordinator | Authentication completed with success")
            return await self.hass.async_add_executor_job(self.device.update)
        except UpdateFailed:
            # Resetting the connection, forces an update during the next run. This is required to prevent
            # a misalignment between the `AlarmDevice` and backend known IDs, needed to implement
            # the long-polling strategy. If IDs are misaligned, then no updates happen and
            # the integration remains stuck.
            _LOGGER.debug(
                "Coordinator | Update failed, resetting IDs to force a full update when the connection is stable"
            )
            self.device.reset()
            raise
