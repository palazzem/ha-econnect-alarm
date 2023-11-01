"""Config flow for E-connect Alarm integration."""
import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from elmo import query as q
from elmo.api.exceptions import CredentialError
from elmo.systems import ELMO_E_CONNECT as E_CONNECT_DEFAULT
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from requests.exceptions import ConnectionError, HTTPError

from .const import (
    CONF_AREAS_ARM_HOME,
    CONF_AREAS_ARM_NIGHT,
    CONF_AREAS_ARM_VACATION,
    CONF_DOMAIN,
    CONF_SCAN_INTERVAL,
    CONF_SYSTEM_NAME,
    CONF_SYSTEM_URL,
    DOMAIN,
    KEY_DEVICE,
    SUPPORTED_SYSTEMS,
)
from .exceptions import InvalidAreas
from .helpers import parse_areas_config, validate_credentials

_LOGGER = logging.getLogger(__name__)


class EconnectConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore
    """Handle a config flow for E-connect Alarm."""

    VERSION = 2
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
            except ConnectionError:
                errors["base"] = "cannot_connect"
            except CredentialError:
                errors["base"] = "invalid_auth"
            except HTTPError as err:
                if 400 <= err.response.status_code <= 499:
                    errors["base"] = "client_error"
                elif 500 <= err.response.status_code <= 599:
                    errors["base"] = "server_error"
                else:
                    _LOGGER.error("Unexpected exception %s", err)
                    errors["base"] = "unknown"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.error("Unexpected exception %s", err)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title="e-Connect/Metronet Alarm", data=user_input)

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
                    vol.Required(
                        CONF_SYSTEM_URL,
                        default=E_CONNECT_DEFAULT,
                        description={"suggested_value": user_input.get(CONF_SYSTEM_URL)},
                    ): vol.In(SUPPORTED_SYSTEMS),
                    vol.Optional(
                        CONF_DOMAIN,
                        description={"suggested_value": user_input.get(CONF_DOMAIN)},
                    ): str,
                    vol.Optional(
                        CONF_SYSTEM_NAME,
                        description={"suggested_value": user_input.get(CONF_SYSTEM_NAME)},
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
        * Areas armed in Arm Vacation state
    """

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Construct."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors = {}
        if user_input is not None:
            try:
                parse_areas_config(user_input.get(CONF_AREAS_ARM_HOME), raises=True)
                parse_areas_config(user_input.get(CONF_AREAS_ARM_NIGHT), raises=True)
                parse_areas_config(user_input.get(CONF_AREAS_ARM_VACATION), raises=True)
            except InvalidAreas:
                errors["base"] = "invalid_areas"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.error("Unexpected exception %s", err)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title="e-Connect/Metronet Alarm", data=user_input)

        # Populate with latest changes or previous settings
        user_input = user_input or {}
        suggest_scan_interval = user_input.get(CONF_SCAN_INTERVAL) or self.config_entry.options.get(CONF_SCAN_INTERVAL)

        # Generate sectors list for user config options
        sectors_list = []
        device = self.hass.data[DOMAIN][self.config_entry.entry_id][KEY_DEVICE]
        for sector_id, item in device._inventory.get(q.SECTORS, {}).items():
            sectors_list.append(f"{item['element']} : {item['name']}")

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_AREAS_ARM_HOME,
                        default=self.config_entry.options.get(CONF_AREAS_ARM_HOME),
                    ): cv.multi_select(sectors_list),
                    vol.Optional(
                        CONF_AREAS_ARM_NIGHT,
                        default=self.config_entry.options.get(CONF_AREAS_ARM_NIGHT),
                    ): cv.multi_select(sectors_list),
                    vol.Optional(
                        CONF_AREAS_ARM_VACATION,
                        default=self.config_entry.options.get(CONF_AREAS_ARM_VACATION),
                    ): cv.multi_select(sectors_list),
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        description={"suggested_value": suggest_scan_interval},
                    ): int,
                }
            ),
            errors=errors,
        )
