"""Decorators used to share the same logic between functions."""
import functools
import logging

from elmo.api.exceptions import LockError

_LOGGER = logging.getLogger(__name__)


def set_device_state(new_state):
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
            self._device.state = new_state
            self.async_write_ha_state()
            try:
                return await func(*args, **kwargs)
            except LockError:
                self._device.state = previous_state
                self.async_write_ha_state()
                _LOGGER.warning("Inserted code is not correct. Retry.")

        return func_wrapper

    return decorator
