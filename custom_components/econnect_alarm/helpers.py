"""Helper methods to reuse common logic across econnect_alarm module."""
from elmo.api.client import ElmoClient

from homeassistant import core
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from .const import BASE_URL, CONF_AREAS_ARM_HOME, CONF_AREAS_ARM_NIGHT, CONF_DOMAIN
from .exceptions import InvalidAreas


def parse_areas_config(config, raises=False):
    """Parse area config that is represented as a comma separated value.

    Usage:
        parse_areas_config("3,4")  # Returns [3, 4]

    Args:
        config: The string that is stored in the configuration registry.
        raises: If set `True`, raises exceptions if they happen.
    Raises:
        ValueError: If given config is not a list of integers.
        AttributeError: If given config is `None` object.
    Returns:
        A Python list with integers representing areas ID, such as `[3, 4]`,
        or `None` if invalid.
    """
    try:
        return [int(x) for x in config.split(",")]
    except (ValueError, AttributeError) as err:
        if raises:
            raise err
        return None


async def validate_credentials(hass: core.HomeAssistant, data):
    """Validate if user input includes valid credentials to connect.

    Initialize the client with an API endpoint and a vendor and authenticate
    your connection to retrieve the access token.

    Args:
        hass: HomeAssistant instance.
        data: data that needs validation (configured username/password).
    Raises:
        ConnectionError: if there is a connection error.
        CredentialError: if given credentials are incorrect.
        HTTPError: if the API backend answers with errors.
    Returns:
        `True` if given `data` includes valid credential checked with
        e-connect backend.
    """
    # Check Credentials
    client = ElmoClient(BASE_URL, domain=data.get(CONF_DOMAIN))
    await hass.async_add_executor_job(
        client.auth, data[CONF_USERNAME], data[CONF_PASSWORD]
    )
    return True


async def validate_areas(hass: core.HomeAssistant, data):
    """Validate if user input is a valid list of areas.

    Args:
        hass: HomeAssistant instance.
        data: data that needs validation (configured areas).
    Raises:
        InvalidAreas: if the given list of areas is not parsable in a
        Python list.
    Returns:
        `True` if given `data` includes properly formatted areas.
    """

    try:
        # Check if areas are parsable
        if data.get(CONF_AREAS_ARM_HOME):
            parse_areas_config(data[CONF_AREAS_ARM_HOME], raises=True)
        if data.get(CONF_AREAS_ARM_NIGHT):
            parse_areas_config(data[CONF_AREAS_ARM_NIGHT], raises=True)
        return True
    except (ValueError, AttributeError):
        raise InvalidAreas
