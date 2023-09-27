import pytest

from custom_components.elmo_iess_alarm.exceptions import InvalidAreas
from custom_components.elmo_iess_alarm.helpers import (
    generate_entity_name,
    parse_areas_config,
)


def test_parse_areas_config_valid_input():
    assert parse_areas_config("3,4") == [3, 4]
    assert parse_areas_config("1,2,3,4,5") == [1, 2, 3, 4, 5]
    assert parse_areas_config("10") == [10]
    assert parse_areas_config("") == []


def test_parse_areas_config_valid_empty_input():
    assert parse_areas_config("", raises=True) == []
    assert parse_areas_config(None, raises=True) == []


def test_parse_areas_config_invalid_input():
    assert parse_areas_config("3,a") == []
    assert parse_areas_config("3.4") == []
    assert parse_areas_config("3,") == []


def test_parse_areas_config_raises_value_error():
    with pytest.raises(InvalidAreas):
        parse_areas_config("3,a", raises=True)
    with pytest.raises(InvalidAreas):
        parse_areas_config("3.4", raises=True)


def test_parse_areas_config_whitespace():
    assert parse_areas_config(" 3 , 4 ") == [3, 4]


def test_generate_entity_name_empty(config_entry):
    assert generate_entity_name(config_entry) == "elmo_iess_alarm_test_user"


def test_generate_entity_name_with_name(config_entry):
    assert generate_entity_name(config_entry, "window") == "elmo_iess_alarm_test_user_window"


def test_generate_entity_name_with_none(config_entry):
    assert generate_entity_name(config_entry, None) == "elmo_iess_alarm_test_user"


def test_generate_entity_name_empty_system(config_entry):
    config_entry.data["system_name"] = "Home"
    assert generate_entity_name(config_entry) == "elmo_iess_alarm_home"


def test_generate_entity_name_with_name_system(config_entry):
    config_entry.data["system_name"] = "Home"
    assert generate_entity_name(config_entry, "window") == "elmo_iess_alarm_home_window"


def test_generate_entity_name_with_none_system(config_entry):
    config_entry.data["system_name"] = "Home"
    assert generate_entity_name(config_entry, None) == "elmo_iess_alarm_home"


def test_generate_entity_name_with_spaces(config_entry):
    config_entry.data["system_name"] = "Home Assistant"
    assert generate_entity_name(config_entry, None) == "elmo_iess_alarm_home_assistant"
