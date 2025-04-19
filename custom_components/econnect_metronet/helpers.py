import logging
from typing import List, Tuple, Union

import voluptuous as vol
from elmo.api.exceptions import CodeError
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.helpers.config_validation import multi_select
from homeassistant.util import slugify

from .const import CONF_SYSTEM_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


class select(multi_select):
    """Extension for the multi_select helper to handle selections of tuples.

    This class extends a multi_select helper class to support tuple-based
    selections, allowing for a more complex selection structure such as
    pairing an identifier with a descriptive string.

    Options are provided as a list of tuples with the following format:
        [(1, 'S1 Living Room'), (2, 'S2 Bedroom'), (3, 'S3 Outdoor')]

    Attributes:
        options (List[Tuple]): A list of tuple options for the select.
        allowed_values (set): A set of valid values (identifiers) that can be selected.
    """

    def __init__(self, options: List[Tuple]) -> None:
        self.options = options
        self.allowed_values = {option[0] for option in options}

    def __call__(self, selected: list) -> list:
        """Validates the input list against the allowed values for selection.

        Args:
            selected: A list of values that have been selected.

        Returns:
            The same list if all selected values are valid.

        Raises:
            vol.Invalid: If the input is not a list or if any of the selected values
                         are not in the allowed values for selection.
        """
        if not isinstance(selected, list):
            raise vol.Invalid("Not a list")

        for value in selected:
            # Reject the value if it's not an option or its identifier
            if value not in self.allowed_values and value not in self.options:
                raise vol.Invalid(f"{value} is not a valid option")

        return selected


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


def split_code(code: str) -> Tuple[str, str]:
    """Splits the given code into two parts: user ID and code.

    The function returns a tuple containing the user ID and the code as separate strings.
    The code is expected to be in the format <USER_ID><CODE> without spaces, with the CODE
    part being the last 6 characters of the string.

    Args:
        code: A string representing the combined user ID and code.

    Returns:
        A tuple of two strings: (user ID, code).

    Raises:
        CodeError: If the input code is less than 7 characters long, indicating it does not
        conform to the expected format.
    """
    if not code:
        raise CodeError("Your code must be in the format <USER_ID><CODE> without spaces.")

    if len(code) < 7:
        _LOGGER.debug("Client | Your configuration may require a code in the format <USER_ID><CODE> without spaces.")
        return "1", code

    user_id_part, code_part = code[:-6], code[-6:]
    if not (user_id_part.isdigit() and code_part.isdigit()):
        raise CodeError("Both user ID and code must be numbers.")

    return user_id_part, code_part
