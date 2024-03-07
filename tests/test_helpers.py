import pytest
from elmo.api.exceptions import CodeError
from homeassistant.core import valid_entity_id

from custom_components.econnect_metronet.helpers import generate_entity_id, split_code


def test_generate_entity_name_empty(config_entry):
    entity_id = generate_entity_id(config_entry)
    assert entity_id == "econnect_metronet.econnect_metronet_test_user"
    assert valid_entity_id(entity_id)


def test_generate_entity_name_with_name(config_entry):
    entity_id = generate_entity_id(config_entry, "window")
    assert entity_id == "econnect_metronet.econnect_metronet_test_user_window"
    assert valid_entity_id(entity_id)


def test_generate_entity_name_with_none(config_entry):
    entity_id = generate_entity_id(config_entry, None)
    assert entity_id == "econnect_metronet.econnect_metronet_test_user"
    assert valid_entity_id(entity_id)


def test_generate_entity_name_empty_system(hass, config_entry):
    hass.config_entries.async_update_entry(config_entry, data={"system_name": "Home"})
    entity_id = generate_entity_id(config_entry)
    assert entity_id == "econnect_metronet.econnect_metronet_home"
    assert valid_entity_id(entity_id)


def test_generate_entity_name_with_name_system(hass, config_entry):
    hass.config_entries.async_update_entry(config_entry, data={"system_name": "Home"})
    entity_id = generate_entity_id(config_entry, "window")
    assert entity_id == "econnect_metronet.econnect_metronet_home_window"
    assert valid_entity_id(entity_id)


def test_generate_entity_name_with_none_system(hass, config_entry):
    hass.config_entries.async_update_entry(config_entry, data={"system_name": "Home"})
    entity_id = generate_entity_id(config_entry, None)
    assert entity_id == "econnect_metronet.econnect_metronet_home"
    assert valid_entity_id(entity_id)


def test_generate_entity_name_with_spaces(hass, config_entry):
    hass.config_entries.async_update_entry(config_entry, data={"system_name": "Home Assistant"})
    entity_id = generate_entity_id(config_entry)
    assert entity_id == "econnect_metronet.econnect_metronet_home_assistant"
    assert valid_entity_id(entity_id)


def test_split_code_with_valid_digits():
    # Should split the numeric user ID and code correctly
    code = "123456789012"
    assert split_code(code) == ("123456", "789012")


def test_split_code_with_exact_six_chars_raises_error():
    # Should raise CodeError for code with less than 7 characters
    code = "123456"
    with pytest.raises(CodeError) as exc_info:
        split_code(code)
    assert "format <USER_ID><CODE> without spaces" in str(exc_info.value)


def test_split_code_with_alphanumeric_user_id_raises_error():
    # Should raise CodeError for alphanumeric user ID
    code = "USER123456"
    with pytest.raises(CodeError) as exc_info:
        split_code(code)
    assert "user ID and code must be numbers" in str(exc_info.value)


def test_split_code_with_special_characters_raises_error():
    # Should raise CodeError for code with special characters
    code = "12345@678901"
    with pytest.raises(CodeError) as exc_info:
        split_code(code)
    assert "user ID and code must be numbers" in str(exc_info.value)


def test_split_code_with_empty_string_raises_error():
    # Should raise CodeError for empty string
    with pytest.raises(CodeError) as exc_info:
        split_code("")
    assert "format <USER_ID><CODE> without spaces" in str(exc_info.value)
