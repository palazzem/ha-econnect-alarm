"""Decorators used to share the same logic between functions."""

import functools
import logging
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any, Concatenate, ParamSpec, Protocol, TypeVar

from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, ServiceCall

from .api.v1.exceptions import CodeError, InvalidToken, LockError
from .const import DOMAIN, KEY_DEVICE
from .devices import AlarmDevice

_LOGGER = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


class DeviceEntity(Protocol):
    """An entity that acts on an alarm device on behalf of a config entry."""

    hass: HomeAssistant
    _config: ConfigEntry
    _device: AlarmDevice

    def async_write_ha_state(self) -> None:
        """Write the entity state to Home Assistant."""


E = TypeVar("E", bound=DeviceEntity)


def set_device_state(
    new_state: AlarmControlPanelState, loader_state: AlarmControlPanelState
) -> Callable[
    [Callable[Concatenate[E, P], Awaitable[R]]],
    Callable[Concatenate[E, P], Coroutine[Any, Any, R | None]],
]:
    """Set a new Alarm device state, or revert to a previous state in case of error.

    This decorator is used to convert a library exception in a log warning, while
    improving the UX by setting an intermediate state while the Alarm device
    is arming/disarming.
    """

    def decorator(
        func: Callable[Concatenate[E, P], Awaitable[R]],
    ) -> Callable[Concatenate[E, P], Coroutine[Any, Any, R | None]]:
        @functools.wraps(func)
        async def func_wrapper(self: E, /, *args: P.args, **kwargs: P.kwargs) -> R | None:
            previous_state = self._device.state
            self._device.state = loader_state
            self.async_write_ha_state()
            try:
                result = await func(self, *args, **kwargs)
                self._device.state = new_state
                self.async_write_ha_state()
                return result
            except LockError:
                _LOGGER.warning(
                    "Impossible to obtain the lock. Be sure you inserted the code, or that nobody is using the panel."
                )
            except CodeError:
                _LOGGER.warning("Inserted code is not correct. Retry.")
            except Exception:
                # All other exceptions are unexpected errors that must revert the state
                _LOGGER.exception(f"Device | Error during operation '{func.__name__}'")
            # Reverting the state in case of any error
            self._device.state = previous_state
            self.async_write_ha_state()
            return None

        return func_wrapper

    return decorator


def retry_refresh_token(
    func: Callable[Concatenate[E, P], Awaitable[R]],
) -> Callable[Concatenate[E, P], Coroutine[Any, Any, R | None]]:
    """Retry an entity coroutine once with a fresh access token.

    When the wrapped coroutine raises `InvalidToken`, the device logs in again with the
    credentials of the entity's config entry and the coroutine runs a second time. A second
    `InvalidToken` is logged and the wrapper returns `None`.
    """

    @functools.wraps(func)
    async def wrapper(self: E, /, *args: P.args, **kwargs: P.kwargs) -> R | None:
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
        return None

    return wrapper


def retry_refresh_token_service(
    func: Callable[[HomeAssistant, str, ServiceCall], Awaitable[R]],
) -> Callable[[HomeAssistant, str, ServiceCall], Coroutine[Any, Any, R | None]]:
    """Retry a service handler once with a fresh access token.

    Like `retry_refresh_token`, for handlers called as `(hass, config_id, call)`: the device
    of `config_id` logs in again with the credentials of the integration's first config entry.
    """

    @functools.wraps(func)
    async def wrapper(hass: HomeAssistant, config_id: str, call: ServiceCall) -> R | None:
        attempts = 0
        while attempts < 2:
            try:
                return await func(hass, config_id, call)
            except InvalidToken as err:
                _LOGGER.debug(f"Device | Invalid access token: {err}")
                if attempts < 1:
                    config = hass.config_entries.async_entries(DOMAIN)[0]
                    device = hass.data[DOMAIN][config_id][KEY_DEVICE]
                    username = config.data[CONF_USERNAME]
                    password = config.data[CONF_PASSWORD]
                    await hass.async_add_executor_job(device.connect, username, password)
                    _LOGGER.debug("Device | Access token has been refreshed")
                attempts += 1
        return None

    return wrapper
