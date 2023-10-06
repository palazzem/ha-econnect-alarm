import pytest
from elmo.api.exceptions import CodeError, LockError

from custom_components.econnect_metronet.decorators import set_device_state


@pytest.mark.asyncio
async def test_set_device_state_successful(alarm_entity):
    """Should update the device state to the new state."""

    @set_device_state("new_state", "loader_state")
    async def test_func(self):
        pass

    # Test
    await test_func(alarm_entity)
    assert alarm_entity._device.state == "new_state"


@pytest.mark.asyncio
async def test_set_device_state_lock_error(alarm_entity):
    """Should revert the device state to the previous state."""

    @set_device_state("new_state", "loader_state")
    async def test_func(self):
        raise LockError()

    # Test
    await test_func(alarm_entity)
    assert alarm_entity._device.state == "unavailable"


@pytest.mark.asyncio
async def test_set_device_state_code_error(alarm_entity):
    """Should revert the device state to the previous state."""

    @set_device_state("new_state", "loader_state")
    async def test_func(self):
        raise CodeError()

    # Test
    await test_func(alarm_entity)
    assert alarm_entity._device.state == "unavailable"


@pytest.mark.asyncio
async def test_set_device_state_loader_state(alarm_entity):
    """Should use the loader_state until the function is completed."""

    @set_device_state("new_state", "loader_state")
    async def test_func(self):
        # Test (what runs here is before the function is completed)
        assert self._device.state == "loader_state"

    # Run test
    await test_func(alarm_entity)
