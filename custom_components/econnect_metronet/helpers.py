from typing import Union

from elmo.api.client import ElmoClient
from homeassistant import core
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.util import slugify

from .const import CONF_DOMAIN, CONF_SYSTEM_NAME, CONF_SYSTEM_URL, DOMAIN
from .exceptions import InvalidAreas


def parse_areas_config(config: str, raises: bool = False):
    """Extracts sector numbers from the provided configuration.

    Parameters:
        config (str or None): A string containing sector configurations in the format "number:name".
            If empty or None, an empty list is returned.
        raises (bool, optional): If True, raises an InvalidAreas exception if there's an error in parsing.
            Defaults to True.

    Returns:
        list: A list of integers representing the extracted sector numbers.

    Raises:
        InvalidAreas: If raises is set to True and there is an error in parsing.

    Example:
        >>> config = "1:sector1 2:sector2 3:sector3"
        >>> parse_areas_config(config)
        [1, 2, 3]
    """
    if config == "" or config is None:
        # Empty config is considered valid (no sectors configured)
        return []
    result = []
    for item in config:
        try:
            number = int(item.split(":")[0])
            result.append(number)
        except (ValueError, AttributeError):
            if raises:
                raise InvalidAreas
            return []
    return result


async def validate_credentials(hass: core.HomeAssistant, config: dict):
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
    client = ElmoClient(config.get(CONF_SYSTEM_URL), domain=config.get(CONF_DOMAIN))
    await hass.async_add_executor_job(client.auth, config.get(CONF_USERNAME), config.get(CONF_PASSWORD))
    return True


def generate_entity_id(config: ConfigEntry, name: Union[str, None] = None) -> str:
    """Generate an entity ID based on system configuration or username.

    Args:
        config (ConfigEntry): The configuration entry from Home Assistant containing system
                              configuration or username.
        name (Union[str, None]): Additional name component to be appended to the entity name.

    Returns:
        str: The generated entity id, which is a combination of the domain and either the configured
             system name or the username, optionally followed by the provided name.

    Example:
        >>> config.data = {"system_name": "Seaside Home"}
        >>> generate_entity_name(entry, "window")
        "elmo_iess_alarm.seaside_home_window"
    """
    # Retrieve the system name or username from the ConfigEntry
    system_name = config.data.get(CONF_SYSTEM_NAME) or config.data.get(CONF_USERNAME)

    # Default to empty string if a name is not provided
    additional_name = name or ""

    # Generate the entity ID and use Home Assistant slugify to ensure it's a valid value
    # NOTE: We append DOMAIN twice as HA removes the domain from the entity ID name. This is unexpected
    # as it means we lose our namespacing, even though this is the suggested method explained in HA documentation.
    # See: https://www.home-assistant.io/faq/unique_id/#can-be-changed
    entity_name = slugify(f"{system_name}_{additional_name}")
    return f"{DOMAIN}.{DOMAIN}_{entity_name}"
