import pytest
from elmo.api.exceptions import CredentialError
from homeassistant import config_entries
from requests.exceptions import ConnectionError, HTTPError
from requests.models import Response
from voluptuous.error import MultipleInvalid

from custom_components.econnect_metronet.const import DOMAIN

from .helpers import _


async def test_form_fields(hass):
    # Ensure the form is properly generated with fields we expect
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert form["type"] == "form"
    assert form["step_id"] == "user"
    assert form["errors"] == {}
    assert form["data_schema"].schema["username"] == str
    assert form["data_schema"].schema["password"] == str
    assert form["data_schema"].schema["domain"] == str


async def test_form_submit_successful_with_input(hass, mocker):
    # Ensure a properly submitted form initializes an ElmoClient
    m_client = mocker.patch(_("config_flow.ElmoClient"))
    m_setup = mocker.patch(_("async_setup"), return_value=True)
    m_setup_entry = mocker.patch(_("async_setup_entry"), return_value=True)
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    # Test
    result = await hass.config_entries.flow.async_configure(
        form["flow_id"],
        {
            "username": "test-username",
            "password": "test-password",
            "domain": "default",
            "system_base_url": "https://metronet.iessonline.com",
        },
    )
    await hass.async_block_till_done()
    # Check Client Authentication
    assert m_client.call_args.args == ("https://metronet.iessonline.com",)
    assert m_client.call_args.kwargs == {"domain": "default"}
    assert m_client().auth.call_count == 1
    assert m_client().auth.call_args.args == ("test-username", "test-password")
    # Check HA setup
    assert len(m_setup.mock_calls) == 1
    assert len(m_setup_entry.mock_calls) == 1
    assert result["type"] == "create_entry"
    assert result["title"] == "e-Connect/Metronet Alarm"
    assert result["data"] == {
        "username": "test-username",
        "password": "test-password",
        "domain": "default",
        "system_base_url": "https://metronet.iessonline.com",
    }


async def test_form_submit_with_defaults(hass, mocker):
    # Ensure a properly submitted form with defaults
    m_client = mocker.patch(_("config_flow.ElmoClient"))
    m_setup = mocker.patch(_("async_setup"), return_value=True)
    m_setup_entry = mocker.patch(_("async_setup_entry"), return_value=True)
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    # Test
    result = await hass.config_entries.flow.async_configure(
        form["flow_id"],
        {
            "username": "test-username",
            "password": "test-password",
            "domain": "default",
        },
    )
    await hass.async_block_till_done()
    assert result["type"] == "create_entry"
    assert result["title"] == "e-Connect/Metronet Alarm"
    assert result["data"] == {
        "username": "test-username",
        "password": "test-password",
        "domain": "default",
        "system_base_url": "https://connect.elmospa.com",
    }
    # Check Client Authentication
    assert m_client.call_args.args == ("https://connect.elmospa.com",)
    assert m_client.call_args.kwargs == {"domain": "default"}
    assert m_client().auth.call_count == 1
    assert m_client().auth.call_args.args == ("test-username", "test-password")
    # Check HA setup
    assert len(m_setup.mock_calls) == 1
    assert len(m_setup_entry.mock_calls) == 1


async def test_form_supported_systems(hass):
    """Test supported systems are pre-loaded in the dropdown."""
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    supported_systems = form["data_schema"].schema["system_base_url"].container
    # Test
    assert supported_systems == {
        "https://connect.elmospa.com": "Elmo e-Connect",
        "https://metronet.iessonline.com": "IESS Metronet",
    }


async def test_form_submit_required_fields(hass, mocker):
    # Ensure the form has the expected required fields
    mocker.patch(_("async_setup"), return_value=True)
    mocker.patch(_("async_setup_entry"), return_value=True)
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    # Test
    with pytest.raises(MultipleInvalid) as excinfo:
        await hass.config_entries.flow.async_configure(form["flow_id"], {})
    await hass.async_block_till_done()
    assert len(excinfo.value.errors) == 3
    errors = []
    errors.append(str(excinfo.value.errors[0]))
    errors.append(str(excinfo.value.errors[1]))
    errors.append(str(excinfo.value.errors[2]))
    assert "required key not provided @ data['username']" in errors
    assert "required key not provided @ data['password']" in errors
    assert "required key not provided @ data['domain']" in errors


async def test_form_submit_wrong_credential(hass, mocker):
    # Ensure the right error is raised for CredentialError exception
    mocker.patch(_("config_flow.ElmoClient"), side_effect=CredentialError)
    mocker.patch(_("async_setup"), return_value=True)
    mocker.patch(_("async_setup_entry"), return_value=True)
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    # Test
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


async def test_form_submit_connection_error(hass, mocker):
    # Ensure the right error is raised for connection errors
    mocker.patch(_("config_flow.ElmoClient"), side_effect=ConnectionError)
    mocker.patch(_("async_setup"), return_value=True)
    mocker.patch(_("async_setup_entry"), return_value=True)
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    # Test
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


async def test_form_client_errors(hass, mocker):
    # Ensure the right error is raised for 4xx API errors
    mocker.patch(_("async_setup"), return_value=True)
    mocker.patch(_("async_setup_entry"), return_value=True)
    m_client = mocker.patch(_("config_flow.ElmoClient.auth"))
    err = HTTPError(response=Response())
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    # Test 400-499 status codes
    for code in range(400, 500):
        err.response.status_code = code
        m_client.side_effect = err
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


async def test_form_server_errors(hass, mocker):
    # Ensure the right error is raised for 5xx API errors
    mocker.patch(_("async_setup"), return_value=True)
    mocker.patch(_("async_setup_entry"), return_value=True)
    m_client = mocker.patch(_("config_flow.ElmoClient.auth"))
    err = HTTPError(response=Response())
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    # Test 500-599 status codes
    for code in range(500, 600):
        err.response.status_code = code
        m_client.side_effect = err
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


async def test_form_unknown_errors(hass, mocker):
    # Ensure we catch unexpected status codes
    mocker.patch(_("async_setup"), return_value=True)
    mocker.patch(_("async_setup_entry"), return_value=True)
    err = HTTPError(response=Response())
    err.response.status_code = 999
    mocker.patch(_("config_flow.ElmoClient.auth"), side_effect=err)
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    # Test non-error status codes
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
    assert result["errors"]["base"] == "unknown"


async def test_form_generic_exception(hass, mocker):
    # Ensure we catch unexpected exceptions
    mocker.patch(_("async_setup"), return_value=True)
    mocker.patch(_("async_setup_entry"), return_value=True)
    mocker.patch(_("config_flow.ElmoClient.auth"), side_effect=Exception("Random Exception"))
    form = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    # Test
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
    assert result["errors"]["base"] == "unknown"
