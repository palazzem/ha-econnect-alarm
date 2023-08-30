"""Exceptions raised by econnect_alarm component."""
from homeassistant.exceptions import HomeAssistantError


class InvalidAreas(HomeAssistantError):
    """Error to indicate given areas are invalid."""
