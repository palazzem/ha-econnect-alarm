"""Exceptions raised by elmo_iess_alarm component."""
from homeassistant.exceptions import HomeAssistantError


class InvalidAreas(HomeAssistantError):
    """Error to indicate given areas are invalid."""
