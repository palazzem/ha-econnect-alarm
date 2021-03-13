"""Test the E-connect Alarm config flow."""
from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.components.econnect_alarm.const import DOMAIN


async def test_form_fields(hass):
    """Test we get the form with the fields we expect."""
    form = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert form["type"] == "form"
    assert form["step_id"] == "user"
    assert form["errors"] == {}
    assert form["data_schema"].schema["username"] == str
    assert form["data_schema"].schema["password"] == str
    assert form["data_schema"].schema["domain"] == str


@patch("homeassistant.components.econnect_alarm.async_setup", return_value=True)
@patch("homeassistant.components.econnect_alarm.async_setup_entry", return_value=True)
@patch("homeassistant.components.econnect_alarm.config_flow.ElmoClient")
async def test_form_submit_successful(mock_client, mock_setup_entry, mock_setup, hass):
    """Test a valid form is properly submitted."""
    form = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        form["flow_id"],
        {
            "username": "test-username",
            "password": "test-password",
            "domain": "test-domain",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == "create_entry"
    assert result["title"] == "E-connect Alarm"
    assert result["data"] == {
        "username": "test-username",
        "password": "test-password",
        "domain": "test-domain",
    }
    # Check HA setup
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1
    # Check Client initialization during validation
    assert ("https://connect.elmospa.com",) == mock_client.call_args.args
    assert {"domain": "test-domain"} == mock_client.call_args.kwargs
    client = mock_client()
    assert client.auth.call_count == 1
    assert ("test-username", "test-password") == client.auth.call_args.args
