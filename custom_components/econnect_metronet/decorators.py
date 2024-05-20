"""Decorators used to share the same logic between functions."""

import functools
import logging

from elmo.api.exceptions import CodeError, InvalidToken, LockError
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from .const import DOMAIN, KEY_DEVICE

_LOGGER = logging.getLogger(__name__)


def set_device_state(new_state, loader_state):
    """Set a new Alarm device state, or revert to a previous state in case of error.

    This decorator is used to convert a library exception in a log warning, while
    improving the UX by setting an intermediate state while the Alarm device
    is arming/disarming.
    """

    def decorator(func):
        @functools.wraps(func)
        async def func_wrapper(*args, **kwargs):
            self = args[0]
            previous_state = self._device.state
            self._device.state = loader_state
            self.async_write_ha_state()
            try:
                result = await func(*args, **kwargs)
                self._device.state = new_state
                self.async_write_ha_state()
                return result
            except LockError:
                _LOGGER.warning(
                    "Impossible to obtain the lock. Be sure you inserted the code, or that nobody is using the panel."
                )
            except CodeError:
                _LOGGER.warning("Inserted code is not correct. Retry.")
            except Exception as err:
                # All other exceptions are unexpected errors that must revert the state
                _LOGGER.error(f"Device | Error during operation '{func.__name__}': {err}")
            # Reverting the state in case of any error
            self._device.state = previous_state
            self.async_write_ha_state()

        return func_wrapper

    return decorator


def retry_refresh_token(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        attempts = 0
        while attempts < 2:
            try:
                return await func(self, *args, **kwargs)
            except InvalidToken as err:
                _LOGGER.debug(f"Device | Invalid access token: {err}")
                if attempts < 1:
                    username = self._config.data[CONF_USERNAME]
                    password = self._config.data[CONF_PASSWORD]
                    await self.hass.async_add_executor_job(self._device.connect, username, password)
                    _LOGGER.debug("Device | Access token has been refreshed")
                attempts += 1

    return wrapper


def retry_refresh_token_service(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        attempts = 0
        while attempts < 2:
            try:
                return await func(*args, **kwargs)
            except InvalidToken as err:
                _LOGGER.debug(f"Device | Invalid access token: {err}")
                if attempts < 1:
                    hass, config_id, _ = args
                    config = hass.config_entries.async_entries(DOMAIN)[0]
                    device = hass.data[DOMAIN][config_id][KEY_DEVICE]
                    username = config.data[CONF_USERNAME]
                    password = config.data[CONF_PASSWORD]
                    await hass.async_add_executor_job(device.connect, username, password)
                    _LOGGER.debug("Device | Access token has been refreshed")
                attempts += 1

    return wrapper
