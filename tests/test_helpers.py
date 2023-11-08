from homeassistant.core import valid_entity_id

from custom_components.econnect_metronet.helpers import generate_entity_id


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


def test_generate_entity_name_empty_system(config_entry):
    config_entry.data["system_name"] = "Home"
    entity_id = generate_entity_id(config_entry)
    assert entity_id == "econnect_metronet.econnect_metronet_home"
    assert valid_entity_id(entity_id)


def test_generate_entity_name_with_name_system(config_entry):
    config_entry.data["system_name"] = "Home"
    entity_id = generate_entity_id(config_entry, "window")
    assert entity_id == "econnect_metronet.econnect_metronet_home_window"
    assert valid_entity_id(entity_id)


def test_generate_entity_name_with_none_system(config_entry):
    config_entry.data["system_name"] = "Home"
    entity_id = generate_entity_id(config_entry, None)
    assert entity_id == "econnect_metronet.econnect_metronet_home"
    assert valid_entity_id(entity_id)


def test_generate_entity_name_with_spaces(config_entry):
    config_entry.data["system_name"] = "Home Assistant"
    entity_id = generate_entity_id(config_entry)
    assert entity_id == "econnect_metronet.econnect_metronet_home_assistant"
    assert valid_entity_id(entity_id)
