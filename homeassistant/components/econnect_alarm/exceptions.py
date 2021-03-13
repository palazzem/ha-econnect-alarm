"""Exceptions raised by econnect_alarm component."""
from homeassistant.exceptions import HomeAssistantError


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class InvalidAreas(HomeAssistantError):
    """Error to indicate given areas are invalid."""
