import logging
from datetime import timedelta
from typing import Any, Dict, Optional

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
    def __init__(self, hass: HomeAssistant, config: ConfigEntry) -> None:
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

        Notes: this is a reimplementation of `async_config_entry_first_refresh` from
        `DataUpdateCoordinator` to handle the authentication and update of the device.
        Eventually, we should avoid doing this and use the `async_config_entry_first_refresh`
        that takes into account possible issues with the configuration.
        """
        username = self.config_entry.data[CONF_USERNAME]
        password = self.config_entry.data[CONF_PASSWORD]
        await self.hass.async_add_executor_job(self.device.connect, username, password)
        await self.hass.async_add_executor_job(self.device.update)
        _LOGGER.debug("Coordinator | First authentication and update are successful")

    async def _async_update_data(self) -> Optional[Dict[str, Any]]:
        """Update device data asynchronously using the long-polling method.

        This method uses the e-Connect long-polling API implemented in `device.has_updates` which
        blocks the thread for up to 15 seconds or until the backend pushes an update.
        A timeout ensures the method doesn't hang indefinitely. In case of invalid token,
        the method attempts to re-authenticate and get an update. If the update fails,
        the connection is reset to ensure proper data alignment in subsequent runs.

        Raises:
            InvalidToken: When the token used for the connection is invalid.
            UpdateFailed: When there's an error in updating the data.

        Notes:
            If the update fails, the method resets the device connection to ensure data
            alignment and prevent the integration from getting stuck.
        """
        try:
            # `device.has_updates` implements e-Connect long-polling API. This
            # action blocks the thread for 15 seconds, or when the backend publishes an update
            # POLLING_TIMEOUT ensures an upper bound regardless of the underlying implementation.
            async with async_timeout.timeout(POLLING_TIMEOUT):
                _LOGGER.debug("Coordinator | Waiting for changes (long-polling)")
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
