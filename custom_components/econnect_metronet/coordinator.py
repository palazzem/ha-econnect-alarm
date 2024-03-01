import logging
from datetime import timedelta
from typing import Any, Dict, Optional

import async_timeout
from elmo.api.exceptions import DeviceDisconnectedError, InvalidToken
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, POLLING_TIMEOUT
from .devices import AlarmDevice

_LOGGER = logging.getLogger(__name__)


class AlarmCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, device: AlarmDevice, scan_interval: int) -> None:
        # Store the device to update the state
        self._device = device

        # Configure the coordinator
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> Optional[Dict[str, Any]]:
        """Update device data asynchronously using the long-polling method.

        This method uses the e-Connect long-polling API implemented in `device.has_updates` which
        blocks the thread for up to 15 seconds or until the backend pushes an update.
        A timeout ensures the method doesn't hang indefinitely.

        In case of invalid token, the method attempts to re-authenticate and get an update.
        If the update fails, the connection is reset to ensure proper data alignment in subsequent runs.

        Returns:
            A dictionary containing the updated data.

        Raises:
            InvalidToken: When the token used for the connection is invalid.
            UpdateFailed: When there's an error in updating the data.
        """
        try:
            if self.data is None:
                # First update, no need to wait for changes
                username = self.config_entry.data[CONF_USERNAME]
                password = self.config_entry.data[CONF_PASSWORD]
                await self.hass.async_add_executor_job(self._device.connect, username, password)
                return await self.hass.async_add_executor_job(self._device.update)

            async with async_timeout.timeout(POLLING_TIMEOUT):
                if not self.last_update_success or not self._device.connected:
                    # Force an update if at least one failed. This is required to prevent
                    # a misalignment between the `AlarmDevice` and backend IDs, needed to implement
                    # the long-polling strategy. If IDs are misaligned, then no updates happen and
                    # the integration remains stuck.
                    # See: https://github.com/palazzem/ha-econnect-alarm/issues/51
                    _LOGGER.debug("Coordinator | Central unit disconnected, forcing a full update")
                    return await self.hass.async_add_executor_job(self._device.update)

                # `device.has_updates` implements e-Connect long-polling API. This
                # action blocks the thread for 15 seconds, or when the backend publishes an update
                # POLLING_TIMEOUT ensures an upper bound regardless of the underlying implementation.
                _LOGGER.debug("Coordinator | Waiting for changes (long-polling)")
                status = await self.hass.async_add_executor_job(self._device.has_updates)
                if status["has_changes"]:
                    _LOGGER.debug("Coordinator | Changes detected, sending an update")
                    return await self.hass.async_add_executor_job(self._device.update)
                else:
                    _LOGGER.debug("Coordinator | No changes detected")
                    return {}
        except InvalidToken:
            # This exception is expected to happen when the token expires. In this case,
            # there is no need to re-raise the exception as it's a normal condition.
            _LOGGER.debug("Coordinator | Invalid token detected, authenticating")
            username = self.config_entry.data[CONF_USERNAME]
            password = self.config_entry.data[CONF_PASSWORD]
            await self.hass.async_add_executor_job(self._device.connect, username, password)
            _LOGGER.debug("Coordinator | Authentication completed with success")
            return await self.hass.async_add_executor_job(self._device.update)
        except DeviceDisconnectedError as err:
            # If the device is disconnected, we keep the previous state and try again later
            # This is required as the device might be temporarily disconnected, and we don't want
            # to make all entities unavailable for a temporary issue. Furthermore, if the device goes
            # in an unavailable state, it might trigger unwanted automations.
            # See: https://github.com/palazzem/ha-econnect-alarm/issues/148
            _LOGGER.error(f"Coordinator | {err}. Keeping the last known state.")
            return {}
