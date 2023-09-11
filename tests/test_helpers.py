import pytest

from custom_components.elmo_iess_alarm.exceptions import InvalidAreas
from custom_components.elmo_iess_alarm.helpers import parse_areas_config


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
