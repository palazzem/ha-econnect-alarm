"""Fixtures that bind a scenario runner to the test's Home Assistant and fake clock."""

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant

from .runner import Scenario


@pytest.fixture
def scenario(hass: HomeAssistant, freezer: FrozenDateTimeFactory, enable_custom_integrations: None) -> Scenario:
    """A scenario runner bound to this test's Home Assistant and fake clock."""
    return Scenario(hass, freezer)
