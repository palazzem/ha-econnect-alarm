from typing import Union

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.util import slugify

from .const import CONF_SYSTEM_NAME, DOMAIN
from .exceptions import InvalidAreas


def parse_areas_config(config: str, raises: bool = False):
    """Parses a comma-separated string of area configurations into a list of integers.

    Takes a string containing comma-separated area IDs and converts it to a list of integers.
    In case of any parsing errors, either raises a custom `InvalidAreas` exception or returns an empty list
    based on the `raises` flag.

    Args:
        config (str): A comma-separated string of area IDs, e.g., "3,4".
        raises (bool, optional): Determines the error handling behavior. If `True`, the function
                                 raises the `InvalidAreas` exception upon encountering a parsing error.
                                 If `False`, it suppresses the error and returns an empty list.
                                 Defaults to `False`.

    Returns:
        list[int]: A list of integers representing area IDs. If parsing fails and `raises` is `False`,
                   returns an empty list.

    Raises:
        InvalidAreas: If there's a parsing error and the `raises` flag is set to `True`.

    Examples:
        >>> parse_areas_config("3,4")
        [3, 4]
        >>> parse_areas_config("3,a")
        []
    """
    if config == "" or config is None:
        # Empty config is considered valid (no sectors configured)
        return []

    try:
        return [int(x) for x in config.split(",")]
    except (ValueError, AttributeError):
        if raises:
            raise InvalidAreas
        return []


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
