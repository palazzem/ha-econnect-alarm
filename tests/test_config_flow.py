"""Test the E-connect Alarm config flow."""
from unittest.mock import patch

import pytest
from elmo.api.exceptions import CredentialError
from homeassistant import config_entries
from requests.exceptions import ConnectionError, HTTPError
from requests.models import Response
from voluptuous.error import MultipleInvalid

from custom_components.elmo_iess_alarm.const import DOMAIN


async def test_form_fields(hass):
    """Test the form is properly generated with fields we expect."""
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert form["type"] == "form"
    assert form["step_id"] == "user"
    assert form["errors"] == {}
    assert form["data_schema"].schema["username"] == str
    assert form["data_schema"].schema["password"] == str
    assert form["data_schema"].schema["domain"] == str


@patch("custom_components.elmo_iess_alarm.async_setup", return_value=True)
@patch("custom_components.elmo_iess_alarm.async_setup_entry", return_value=True)
@patch("custom_components.elmo_iess_alarm.helpers.ElmoClient")
async def test_form_submit_successful(mock_client, mock_setup_entry, mock_setup, hass):
    """Test a properly submitted form initializes an ElmoClient."""
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    result = await hass.config_entries.flow.async_configure(
        form["flow_id"],
        {
            "username": "test-username",
            "password": "test-password",
            "domain": "test-domain",
            "system_base_url": "https://connect.elmospa.com",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == "create_entry"
    assert result["title"] == "E-connect Alarm"
    assert result["data"] == {
        "username": "test-username",
        "password": "test-password",
        "domain": "test-domain",
        "system_base_url": "https://connect.elmospa.com",
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


@patch("custom_components.elmo_iess_alarm.async_setup", return_value=True)
@patch("custom_components.elmo_iess_alarm.async_setup_entry", return_value=True)
@patch("custom_components.elmo_iess_alarm.helpers.ElmoClient")
async def test_form_submit_with_defaults(mock_client, mock_setup_entry, mock_setup, hass):
    """Test a properly submitted form with defaults."""
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    result = await hass.config_entries.flow.async_configure(
        form["flow_id"],
        {
            "username": "test-username",
            "password": "test-password",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == "create_entry"
    assert result["title"] == "E-connect Alarm"
    assert result["data"] == {
        "username": "test-username",
        "password": "test-password",
        "system_base_url": "https://connect.elmospa.com",
    }
    # Check HA setup
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1
    # Check Client defaults initialization during validation
    assert ("https://connect.elmospa.com",) == mock_client.call_args.args


async def test_form_supported_systems(hass):
    """Test supported systems are pre-loaded in the dropdown."""
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    supported_systems = form["data_schema"].schema["system_base_url"].container
    # Test
    assert supported_systems == {
        "https://connect.elmospa.com": "Elmo e-Connect",
        "https://metronet.iessonline.com": "IESS Metronet",
    }


@patch("custom_components.elmo_iess_alarm.async_setup", return_value=True)
@patch("custom_components.elmo_iess_alarm.async_setup_entry", return_value=True)
async def test_form_submit_required_fields(mock_setup_entry, mock_setup, hass):
    """Test the form has the expected required fields."""
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    with pytest.raises(MultipleInvalid) as excinfo:
        await hass.config_entries.flow.async_configure(form["flow_id"], {})
    await hass.async_block_till_done()

    assert len(excinfo.value.errors) == 2
    errors = []
    errors.append(str(excinfo.value.errors[0]))
    errors.append(str(excinfo.value.errors[1]))
    assert "required key not provided @ data['username']" in errors
    assert "required key not provided @ data['password']" in errors


@patch("custom_components.elmo_iess_alarm.async_setup", return_value=True)
@patch("custom_components.elmo_iess_alarm.async_setup_entry", return_value=True)
@patch(
    "custom_components.elmo_iess_alarm.helpers.ElmoClient.auth",
    side_effect=CredentialError,
)
async def test_form_submit_wrong_credential(mock_client, mock_setup_entry, mock_setup, hass):
    """Test the right error is raised for CredentialError exception."""
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    result = await hass.config_entries.flow.async_configure(
        form["flow_id"],
        {
            "username": "test-username",
            "password": "test-password",
            "domain": "test-domain",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == "form"
    assert result["errors"]["base"] == "invalid_auth"


@patch("custom_components.elmo_iess_alarm.async_setup", return_value=True)
@patch("custom_components.elmo_iess_alarm.async_setup_entry", return_value=True)
@patch(
    "custom_components.elmo_iess_alarm.helpers.ElmoClient.auth",
    side_effect=ConnectionError,
)
async def test_form_submit_connection_error(mock_client, mock_setup_entry, mock_setup, hass):
    """Test the right error is raised for connection errors."""
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    result = await hass.config_entries.flow.async_configure(
        form["flow_id"],
        {
            "username": "test-username",
            "password": "test-password",
            "domain": "test-domain",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == "form"
    assert result["errors"]["base"] == "cannot_connect"


@patch("custom_components.elmo_iess_alarm.async_setup", return_value=True)
@patch("custom_components.elmo_iess_alarm.async_setup_entry", return_value=True)
async def test_form_client_errors(mock_setup_entry, mock_setup, hass):
    """Test the right error is raised for 4xx API errors."""
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    # Check all 4xx errors
    r = Response()
    for code in range(400, 500):
        r.status_code = code
        err = HTTPError(response=r)

        with patch(
            "custom_components.elmo_iess_alarm.helpers.ElmoClient.auth",
            side_effect=err,
        ):
            result = await hass.config_entries.flow.async_configure(
                form["flow_id"],
                {
                    "username": "test-username",
                    "password": "test-password",
                    "domain": "test-domain",
                },
            )
            await hass.async_block_till_done()

            assert result["type"] == "form"
            assert result["errors"]["base"] == "client_error"


@patch("custom_components.elmo_iess_alarm.async_setup", return_value=True)
@patch("custom_components.elmo_iess_alarm.async_setup_entry", return_value=True)
async def test_form_server_errors(mock_setup_entry, mock_setup, hass):
    """Test the right error is raised for 5xx API errors."""
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    # Check all 5xx errors
    r = Response()
    for code in range(500, 600):
        r.status_code = code
        err = HTTPError(response=r)

        with patch(
            "custom_components.elmo_iess_alarm.helpers.ElmoClient.auth",
            side_effect=err,
        ):
            result = await hass.config_entries.flow.async_configure(
                form["flow_id"],
                {
                    "username": "test-username",
                    "password": "test-password",
                    "domain": "test-domain",
                },
            )
            await hass.async_block_till_done()

            assert result["type"] == "form"
            assert result["errors"]["base"] == "server_error"
