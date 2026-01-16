import pytest
from homeassistant.data_entry_flow import InvalidData
from homeassistant.helpers.config_validation import multi_select as select

from custom_components.econnect_metronet.const import DOMAIN, KEY_DEVICE


class TestOptionsFlow:
    @pytest.fixture(autouse=True)
    def setup(self, hass, config_entry, alarm_device):
        self.hass = hass
        self.config_entry = config_entry
        # Mock integration setup
        config_entry.add_to_hass(hass)
        hass.data[DOMAIN][config_entry.entry_id] = {
            KEY_DEVICE: alarm_device,
        }

    async def test_form_fields(self, hass, config_entry):
        # Ensure form is loaded with the correct fields
        form = await hass.config_entries.options.async_init(
            config_entry.entry_id, context={"show_advanced_options": False}
        )
        assert form["type"] == "form"
        assert form["step_id"] == "init"
        assert form["errors"] == {}
        assert list(form["data_schema"].schema.keys()) == [
            "areas_arm_away",
            "areas_arm_home",
            "areas_arm_night",
            "areas_arm_vacation",
            "scan_interval",
        ]
        assert isinstance(form["data_schema"].schema["areas_arm_away"], select)
        assert isinstance(form["data_schema"].schema["areas_arm_home"], select)
        assert isinstance(form["data_schema"].schema["areas_arm_night"], select)
        assert isinstance(form["data_schema"].schema["areas_arm_vacation"], select)
        assert form["data_schema"].schema["scan_interval"] == int

    async def test_form_submit_successful_empty(self, hass, config_entry):
        # Ensure an empty form can be submitted successfully
        form = await hass.config_entries.options.async_init(
            config_entry.entry_id, context={"show_advanced_options": False}
        )
        # Test
        result = await hass.config_entries.options.async_configure(
            form["flow_id"],
            user_input={},
        )
        await hass.async_block_till_done()
        # Check HA config
        assert result["type"] == "create_entry"
        assert result["title"] == "e-Connect/Metronet Alarm"
        assert result["data"] == {
            "areas_arm_vacation": [],
            "areas_arm_home": [],
            "areas_arm_night": [],
            "areas_arm_away": [],
        }

    async def test_form_submit_invalid_type(self, hass, config_entry):
        # Ensure it fails if a user submits an option with an invalid type
        form = await hass.config_entries.options.async_init(
            config_entry.entry_id, context={"show_advanced_options": False}
        )
        # Test
        with pytest.raises(InvalidData) as excinfo:
            await hass.config_entries.options.async_configure(
                form["flow_id"],
                user_input={
                    "areas_arm_home": "1",
                },
            )
            await hass.async_block_till_done()
        assert excinfo.value.schema_errors["areas_arm_home"] == "Not a list"

    async def test_form_submit_invalid_input(self, hass, config_entry):
        # Ensure it fails if a user submits an option not in the allowed list
        form = await hass.config_entries.options.async_init(
            config_entry.entry_id, context={"show_advanced_options": False}
        )
        # Test
        with pytest.raises(InvalidData) as excinfo:
            await hass.config_entries.options.async_configure(
                form["flow_id"],
                user_input={
                    "areas_arm_home": [
                        (3, "Garden"),
                    ],
                },
            )
            await hass.async_block_till_done()
        assert excinfo.value.schema_errors["areas_arm_home"] == "(3, 'Garden') is not a valid option"

    async def test_form_submit_successful_with_identifier(self, hass, config_entry):
        # Ensure users can submit an option just by using the option ID
        form = await hass.config_entries.options.async_init(
            config_entry.entry_id, context={"show_advanced_options": False}
        )
        # Test
        result = await hass.config_entries.options.async_configure(
            form["flow_id"],
            user_input={
                "areas_arm_home": [1],
            },
        )
        await hass.async_block_till_done()
        # Check HA config
        assert result["type"] == "create_entry"
        assert result["title"] == "e-Connect/Metronet Alarm"
        assert result["data"] == {
            "areas_arm_away": [],
            "areas_arm_home": [1],
            "areas_arm_night": [],
            "areas_arm_vacation": [],
        }

    async def test_form_submit_successful_with_input(self, hass, config_entry):
        # Ensure users can submit an option that is available in the allowed list
        form = await hass.config_entries.options.async_init(
            config_entry.entry_id, context={"show_advanced_options": False}
        )
        # Test
        result = await hass.config_entries.options.async_configure(
            form["flow_id"],
            user_input={
                "areas_arm_home": [
                    (1, "S1 Living Room"),
                ],
            },
        )
        await hass.async_block_till_done()
        # Check HA config
        assert result["type"] == "create_entry"
        assert result["title"] == "e-Connect/Metronet Alarm"
        assert result["data"] == {
            "areas_arm_away": [],
            "areas_arm_home": [(1, "S1 Living Room")],
            "areas_arm_night": [],
            "areas_arm_vacation": [],
        }

    async def test_form_submit_successful_with_multiple_inputs(self, hass, config_entry):
        # Ensure multiple options can be submitted at once
        form = await hass.config_entries.options.async_init(
            config_entry.entry_id, context={"show_advanced_options": False}
        )
        # Test
        result = await hass.config_entries.options.async_configure(
            form["flow_id"],
            user_input={
                "areas_arm_away": [
                    (2, "S2 Bedroom"),
                ],
                "areas_arm_home": [
                    (1, "S1 Living Room"),
                ],
                "areas_arm_night": [
                    (1, "S1 Living Room"),
                ],
                "areas_arm_vacation": [(1, "S1 Living Room"), (2, "S2 Bedroom")],
            },
        )
        await hass.async_block_till_done()
        # Check HA config
        assert result["type"] == "create_entry"
        assert result["title"] == "e-Connect/Metronet Alarm"
        assert result["data"] == {
            "areas_arm_away": [(2, "S2 Bedroom")],
            "areas_arm_home": [(1, "S1 Living Room")],
            "areas_arm_night": [(1, "S1 Living Room")],
            "areas_arm_vacation": [(1, "S1 Living Room"), (2, "S2 Bedroom")],
        }
