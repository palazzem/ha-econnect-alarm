"""Config flow for E-connect Alarm integration."""
import logging

from elmo.api.client import ElmoClient
from requests.exceptions import ConnectionError, HTTPError
import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from .const import BASE_URL, CONF_VENDOR, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_VENDOR, default=""): str,
    }
)


class EconnectConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for E-connect Alarm."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial configuration."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # Initialize the client with an API endpoint and a vendor and
    # authenticate your connection to retrieve the access token
    # TODO: Simplify the API to accept no vendor
    client = ElmoClient(BASE_URL, data["vendor"])

    # TODO: Use a custom exception in ElmoClient instead of requests.exceptions
    try:
        await hass.async_add_executor_job(
            client.auth, data["username"], data["password"]
        )
    except HTTPError:
        # Wrong credentials
        # TODO: use the custom exception instead of redefining a new exception
        raise InvalidAuth
    except ConnectionError:
        # Unable to connect
        # TODO: use the custom exception instead of redefining a new exception
        raise CannotConnect

    # Return info that you want to store in the config entry
    return {"title": "E-connect Alarm"}
