import pytest

pytest_plugins = ["tests.hass.fixtures"]


@pytest.fixture
async def hass(hass):
    hass.data["custom_components"] = None
    yield hass
