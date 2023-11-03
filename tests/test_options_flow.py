import pytest
from voluptuous.error import MultipleInvalid


async def test_form_fields(hass, config_entry):
    config_entry.add_to_hass(hass)
    # Test
    form = await hass.config_entries.options.async_init(config_entry.entry_id, context={"show_advanced_options": False})
    assert form["type"] == "form"
    assert form["step_id"] == "init"
    assert form["errors"] == {}
    assert list(form["data_schema"].schema.keys()) == [
        "areas_arm_home",
        "areas_arm_night",
        "areas_arm_vacation",
        "scan_interval",
    ]
    assert form["data_schema"].schema["areas_arm_home"] == str
    assert form["data_schema"].schema["areas_arm_night"] == str
    assert form["data_schema"].schema["areas_arm_vacation"] == str
    assert form["data_schema"].schema["scan_interval"] == int


async def test_form_submit_successful_empty(hass, config_entry):
    # Ensure an empty form can be submitted successfully
    config_entry.add_to_hass(hass)
    form = await hass.config_entries.options.async_init(config_entry.entry_id, context={"show_advanced_options": False})
    # Test
    result = await hass.config_entries.options.async_configure(
        form["flow_id"],
        user_input={},
    )
    await hass.async_block_till_done()
    # Check HA setup
    assert result["type"] == "create_entry"
    assert result["title"] == "e-Connect/Metronet Alarm"
    assert result["data"] == {}


async def test_form_submit_successful_with_input(hass, config_entry):
    # Ensure a single field can be submitted successfully
    config_entry.add_to_hass(hass)
    form = await hass.config_entries.options.async_init(config_entry.entry_id, context={"show_advanced_options": False})
    # Test
    result = await hass.config_entries.options.async_configure(
        form["flow_id"],
        user_input={
            "areas_arm_home": "1",
        },
    )
    await hass.async_block_till_done()
    # Check HA setup
    assert result["type"] == "create_entry"
    assert result["title"] == "e-Connect/Metronet Alarm"
    assert result["data"] == {"areas_arm_home": "1"}


async def test_form_submit_fails_with_none(hass, config_entry):
    # Ensure an expected error is raised when submitting an invalid type
    config_entry.add_to_hass(hass)
    form = await hass.config_entries.options.async_init(config_entry.entry_id, context={"show_advanced_options": False})
    # Test
    with pytest.raises(MultipleInvalid) as excinfo:
        await hass.config_entries.options.async_configure(
            form["flow_id"],
            user_input={
                "areas_arm_home": None,
            },
        )
        await hass.async_block_till_done()

    assert excinfo.value.errors[0].msg == "expected str"
