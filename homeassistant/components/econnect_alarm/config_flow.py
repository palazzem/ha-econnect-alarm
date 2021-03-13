"""Config flow for E-connect Alarm integration."""
import logging

from elmo.api.client import ElmoClient
from elmo.api.exceptions import CredentialError
from requests.exceptions import ConnectionError
import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback

from .const import (
    BASE_URL,
    CONF_AREAS_ARM_HOME,
    CONF_AREAS_ARM_NIGHT,
    CONF_DOMAIN,
    DOMAIN,
)
from .helpers import parse_areas_config

_LOGGER = logging.getLogger(__name__)


class EconnectConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for E-connect Alarm."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Implement OptionsFlow."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial configuration."""
        errors = {}
        if user_input is not None:
            try:
                # Validate submitted configuration
                await validate_credentials(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.error(f"Unexpected exception {err}")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title="E-connect Alarm", data=user_input)

        # Populate with latest changes
        user_input = user_input or {}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        description={"suggested_value": user_input.get(CONF_USERNAME)},
                    ): str,
                    vol.Required(
                        CONF_PASSWORD,
                        description={"suggested_value": user_input.get(CONF_PASSWORD)},
                    ): str,
                    vol.Optional(
                        CONF_DOMAIN,
                        description={"suggested_value": user_input.get(CONF_DOMAIN)},
                    ): str,
                }
            ),
            errors=errors,
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Reconfigure integration options.

    Available options are:
        * Areas armed in Arm Away state
        * Areas armed in Arm Night state
    """

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Construct."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors = {}
        if user_input is not None:
            try:
                await validate_areas(self.hass, user_input)
            except InvalidAreas:
                errors["base"] = "invalid_areas"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.error(f"Unexpected exception {err}")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title="E-connect Alarm", data=user_input)

        # Populate with latest changes or previous settings
        user_input = user_input or {}
        suggest_arm_home = user_input.get(
            CONF_AREAS_ARM_HOME
        ) or self.config_entry.options.get(CONF_AREAS_ARM_HOME)
        suggest_arm_night = user_input.get(
            CONF_AREAS_ARM_NIGHT
        ) or self.config_entry.options.get(CONF_AREAS_ARM_NIGHT)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_AREAS_ARM_HOME,
                        description={"suggested_value": suggest_arm_home},
                    ): str,
                    vol.Optional(
                        CONF_AREAS_ARM_NIGHT,
                        description={"suggested_value": suggest_arm_night},
                    ): str,
                }
            ),
            errors=errors,
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""


class InvalidAreas(exceptions.HomeAssistantError):
    """Error to indicate given areas are invalid."""


async def validate_credentials(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Initialize the client with an API endpoint and a vendor and authenticate
    your connection to retrieve the access token.
    """

    try:
        # Check Credentials
        client = ElmoClient(BASE_URL, domain=data.get(CONF_DOMAIN))
        return await hass.async_add_executor_job(
            client.auth, data[CONF_USERNAME], data[CONF_PASSWORD]
        )
    except CredentialError:
        raise InvalidAuth
    except ConnectionError:
        raise CannotConnect


async def validate_areas(hass: core.HomeAssistant, data):
    """Validate if user input is a valid list of areas."""

    try:
        # Check if areas are parsable
        if data.get(CONF_AREAS_ARM_HOME):
            parse_areas_config(data[CONF_AREAS_ARM_HOME], raises=True)
        if data.get(CONF_AREAS_ARM_NIGHT):
            parse_areas_config(data[CONF_AREAS_ARM_NIGHT], raises=True)
    except (ValueError, AttributeError):
        raise InvalidAreas
