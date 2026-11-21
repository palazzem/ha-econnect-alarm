import gc
import logging
import weakref

import pytest
import responses
from requests.exceptions import HTTPError

from custom_components.econnect_metronet.api.v1 import query
from custom_components.econnect_metronet.api.v1.client import ElmoClient
from custom_components.econnect_metronet.api.v1.exceptions import (
    CodeError,
    CommandError,
    CredentialError,
    DeviceDisconnectedError,
    InvalidToken,
    LockError,
    LockNotAcquired,
    ParseError,
    QueryNotValid,
)
from custom_components.econnect_metronet.api.v1.systems import ELMO_E_CONNECT, IESS_METRONET

from .fixtures import responses as r


def test_client_constructor_default():
    """Should build the client using the default values."""
    client = ElmoClient()
    assert client._router._base_url == "https://connect.elmospa.com"
    assert client._domain is None
    assert client._session_id is None
    assert client._panel is None


def test_client_econnect_system():
    """Should build the client using Elmo e-Connect URL."""
    client = ElmoClient(ELMO_E_CONNECT)
    assert client._router._base_url == "https://connect.elmospa.com"
    assert client._domain is None
    assert client._session_id is None
    assert client._panel is None


def test_client_metronet_system():
    """Should build the client using IESS Metronet URL."""
    client = ElmoClient(IESS_METRONET)
    assert client._router._base_url == "https://metronet.iessonline.com"
    assert client._domain is None
    assert client._session_id is None
    assert client._panel is None


def test_client_constructor_v03():
    """Backward compatibility pre 0.4: the order of parameters must not change
    otherwise a breaking change is introduced.
    """
    client = ElmoClient("https://example.com", "domain")
    assert client._router._base_url == "https://example.com"
    assert client._domain == "domain"
    assert client._session_id is None
    assert client._panel is None


def test_client_constructor():
    """Should build the client using the base URL and the domain suffix."""
    client = ElmoClient(base_url="https://example.com", domain="domain")
    assert client._router._base_url == "https://example.com"
    assert client._domain == "domain"
    assert client._session_id is None
    assert client._panel is None


def test_client_constructor_with_session_id():
    """Should build the client with a provided `session_id`."""
    client = ElmoClient(session_id="test")
    assert client._session_id == "test"


def test_client_auth_success(server):
    """Should authenticate with valid credentials."""
    server.add(responses.GET, "https://example.com/api/login", body=r.LOGIN, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    # Test
    assert client.auth("test", "test") == "00000000-0000-0000-0000-000000000000"
    assert client._session_id == "00000000-0000-0000-0000-000000000000"
    assert len(server.calls) == 1


def test_client_debug_with_session_sanitized(server, caplog):
    """Ensure that the session ID is sanitized in debug mode."""
    server.add(responses.GET, "https://example.com/api/login", body=r.LOGIN, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    caplog.set_level(logging.DEBUG)
    # Test
    assert client.auth("test", "test") == "00000000-0000-0000-0000-000000000000"
    assert "Authentication successful: 00000000-XXXX-XXXX-XXXX-XXXXXXXXXXXX" in caplog.text


def test_client_auth_stores_panel_details(server):
    """Should store panel details after login is successful."""
    server.add(responses.GET, "https://example.com/api/login", body=r.LOGIN, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    # Test
    client.auth("test", "test")
    assert client._panel == {
        "description": "T-800 1.0.1",
        "last_connection": "01/01/1984 13:27:28",
        "last_disconnection": "01/10/1984 13:27:18",
        "major": 1,
        "minor": 0,
        "source_ip": "10.0.0.1",
        "connection_type": "EthernetWiFi",
        "device_class": 92,
        "revision": 1,
        "build": 1,
        "brand": 0,
        "language": 0,
        "areas": 4,
        "sectors_per_area": 4,
        "total_sectors": 16,
        "inputs": 24,
        "outputs": 24,
        "operators": 64,
        "sectors_in_use": [
            True,
            True,
            True,
            True,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
        ],
        "model": "T-800",
        "login_without_user_id": True,
        "additional_info_supported": 1,
        "is_fire_panel": False,
    }
    assert len(server.calls) == 1


def test_client_auth_no_panel_details(server):
    """Should be resilient if the `Panel` key is missing."""
    html = """
        {
            "SessionId": "00000000-0000-0000-0000-000000000000",
            "Username": "test",
            "Domain": "domain",
            "Language": "en",
            "IsActivated": true,
            "IsConnected": true,
            "IsLoggedIn": false,
            "IsLoginInProgress": false,
            "CanElevate": true,
            "AccountId": 100,
            "IsManaged": false,
            "Redirect": false,
            "IsElevation": false
        }
    """
    server.add(responses.GET, "https://example.com/api/login", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    # Test
    client.auth("test", "test")
    assert client._panel == {}
    assert len(server.calls) == 1


def test_client_auth_forbidden(server):
    """Should raise an exception if credentials are not valid."""
    server.add(
        responses.GET,
        "https://example.com/api/login",
        body="Username or Password is invalid",
        status=403,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    # Test
    with pytest.raises(CredentialError):
        client.auth("test", "test")
    assert client._session_id is None
    assert client._panel is None
    assert len(server.calls) == 1


def test_client_auth_unknown_error(server):
    """Should raise an exception if there is an unknown error."""
    server.add(responses.GET, "https://example.com/api/login", body="Server Error", status=500)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    # Test
    with pytest.raises(HTTPError):
        client.auth("test", "test")
    assert client._session_id is None
    assert client._panel is None
    assert len(server.calls) == 1


def test_client_auth_redirect(server):
    """Should update the client Router if a redirect is required."""
    redirect = """
        {
            "SessionId": "00000000-0000-0000-0000-000000000000",
            "Domain": "domain",
            "Redirect": true,
            "RedirectTo": "https://redirect.example.com"
        }
    """
    login = """
        {
            "SessionId": "99999999-9999-9999-9999-999999999999",
            "Username": "test",
            "Domain": "domain",
            "Language": "en",
            "IsActivated": true,
            "IsConnected": true,
            "IsLoggedIn": false,
            "IsLoginInProgress": false,
            "CanElevate": true,
            "AccountId": 100,
            "IsManaged": false,
            "Redirect": false,
            "IsElevation": false
        }
    """
    server.add(responses.GET, "https://example.com/api/login", body=redirect, status=200)
    server.add(responses.GET, "https://redirect.example.com/api/login", body=login, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    # Test
    assert client.auth("test", "test")
    assert client._router._base_url == "https://redirect.example.com"
    assert client._session_id == "99999999-9999-9999-9999-999999999999"
    assert len(server.calls) == 2


def test_client_auth_redirect_web_login_econnect(server):
    """Ensure web login session token is used when redirect is required.
    Regression test: https://github.com/palazzem/econnect-python/issues/158
    """
    redirect = """
        {
            "SessionId": "00000000-0000-0000-0000-000000000000",
            "Domain": "domain",
            "Redirect": true,
            "RedirectTo": "https://redirect.example.com"
        }
    """
    login = """
        {
            "SessionId": "99999999-9999-9999-9999-999999999999",
            "Username": "test",
            "Domain": "domain",
            "Language": "en",
            "IsActivated": true,
            "IsConnected": true,
            "IsLoggedIn": false,
            "IsLoginInProgress": false,
            "CanElevate": true,
            "AccountId": 100,
            "IsManaged": false,
            "Redirect": false,
            "IsElevation": false
        }
    """
    server.add(responses.GET, "https://connect.elmospa.com/api/login", body=redirect, status=200)
    server.add(responses.GET, "https://redirect.example.com/api/login", body=login, status=200)
    server.add(responses.POST, "https://webservice.elmospa.com/domain", body=r.STATUS_PAGE, status=200)
    client = ElmoClient(base_url=ELMO_E_CONNECT, domain="domain")
    # Test
    assert client.auth("test", "test")
    assert len(server.calls) == 3
    assert client._router._base_url == "https://redirect.example.com"
    assert client._session_id == "f8h23b4e-7a9f-4d3f-9b08-2769263ee33c"


def test_client_auth_redirect_web_login_metronet(server):
    """Ensure web login session token is used when redirect is required.
    Regression test: https://github.com/palazzem/econnect-python/issues/168
    """
    redirect = """
        {
            "SessionId": "00000000-0000-0000-0000-000000000000",
            "Domain": "domain",
            "Redirect": true,
            "RedirectTo": "https://redirect.example.com"
        }
    """
    login = """
        {
            "SessionId": "99999999-9999-9999-9999-999999999999",
            "Username": "test",
            "Domain": "domain",
            "Language": "en",
            "IsActivated": true,
            "IsConnected": true,
            "IsLoggedIn": false,
            "IsLoginInProgress": false,
            "CanElevate": true,
            "AccountId": 100,
            "IsManaged": false,
            "Redirect": false,
            "IsElevation": false
        }
    """
    server.add(responses.GET, "https://metronet.iessonline.com/api/login", body=redirect, status=200)
    server.add(responses.GET, "https://redirect.example.com/api/login", body=login, status=200)
    server.add(responses.POST, "https://metronet.iessonline.com/domain", body=r.STATUS_PAGE, status=200)
    client = ElmoClient(base_url=IESS_METRONET, domain="domain")
    # Test
    assert client.auth("test", "test")
    assert len(server.calls) == 3
    assert client._router._base_url == "https://redirect.example.com"
    assert client._session_id == "f8h23b4e-7a9f-4d3f-9b08-2769263ee33c"


def test_client_auth_infinite_redirect(server):
    """Should prevent infinite redirects in the auth() call."""
    redirect = """
        {
            "SessionId": "00000000-0000-0000-0000-000000000000",
            "Domain": "domain",
            "Redirect": true,
            "RedirectTo": "https://redirect.example.com"
        }
    """
    server.add(responses.GET, "https://example.com/api/login", body=redirect, status=200)
    server.add(
        responses.GET,
        "https://redirect.example.com/api/login",
        body=redirect,
        status=200,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    # Test
    assert client.auth("test", "test")
    assert client._router._base_url == "https://redirect.example.com"
    assert client._session_id == "00000000-0000-0000-0000-000000000000"
    assert len(server.calls) == 2


def test_client_auth_without_domain(server):
    """Should authenticate without sending the domain field."""
    html = """
        {
            "SessionId": "00000000-0000-0000-0000-000000000000",
            "Redirect": false
        }
    """
    server.add(responses.GET, "https://example.com/api/login", body=html, status=200)
    client = ElmoClient(base_url="https://example.com")
    # Test
    client.auth("test", "test")
    assert len(server.calls) == 1
    assert "domain" not in server.calls[0].request.params


def test_client_auth_with_domain(server):
    """Should authenticate sending the domain field."""
    html = """
        {
            "SessionId": "00000000-0000-0000-0000-000000000000",
            "Redirect": false
        }
    """
    server.add(responses.GET, "https://example.com/api/login", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    # Test
    client.auth("test", "test")
    assert len(server.calls) == 1
    assert server.calls[0].request.params["domain"] == "domain"


def test_client_poll(server):
    """Should leverage long-polling endpoint to grab the status."""
    html = """
        {
            "ConnectionStatus": false,
            "CanElevate": false,
            "LoggedIn": false,
            "LoginInProgress": false,
            "Areas": false,
            "Events": false,
            "Inputs": false,
            "Outputs": false,
            "Anomalies": false,
            "ReadStringsInProgress": false,
            "ReadStringPercentage": 0,
            "Strings": 0,
            "ManagedAccounts": false,
            "Temperature": false,
            "StatusAdv": false,
            "Images": false,
            "AdditionalInfoSupported": true,
            "HasChanges": false
        }
    """
    server.add(responses.POST, "https://example.com/api/updates", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    ids = {
        query.SECTORS: 42,
        query.INPUTS: 4242,
        query.OUTPUTS: 424,
        query.ALERTS: 424242,
    }
    # Test
    state = client.poll(ids)
    assert len(state.keys()) == 5
    # Check response
    assert state["has_changes"] is False
    assert state["inputs"] is False
    assert state["areas"] is False
    assert state["outputs"] is False
    assert state["statusadv"] is False
    # Check request
    body = server.calls[0].request.body.split("&")
    assert "sessionId=test" in body
    assert "Areas=42" in body
    assert "Inputs=4242" in body
    assert "Outputs=424" in body
    assert "CanElevate=1" in body
    assert "ConnectionStatus=1" in body


def test_client_auth_econnect_web_login(server):
    """Ensure API and Web login are executed when using e-Connect cloud API.
    Regression test: https://github.com/palazzem/econnect-python/issues/158
    """
    server.add(responses.GET, "https://connect.elmospa.com/api/login", body=r.LOGIN, status=200)
    server.add(responses.POST, "https://webservice.elmospa.com/domain", body=r.STATUS_PAGE, status=200)
    client = ElmoClient(base_url=ELMO_E_CONNECT, domain="domain")
    # Test
    client.auth("test", "test")
    assert len(server.calls) == 2
    request_body = dict(item.split("=") for item in server.calls[1].request.body.split("&"))
    assert client._session_id == "f8h23b4e-7a9f-4d3f-9b08-2769263ee33c"
    assert request_body == {
        "IsDisableAccountCreation": "True",
        "IsAllowThemeChange": "True",
        "UserName": "test",
        "Password": "test",
        "RememberMe": "false",
    }


def test_client_auth_econnect_web_login_with_default_domain(server):
    """Ensure API and Web login are executed when using e-Connect cloud API.
    Regression test: https://github.com/palazzem/econnect-python/issues/158
    """
    server.add(responses.GET, "https://connect.elmospa.com/api/login", body=r.LOGIN, status=200)
    server.add(responses.POST, "https://webservice.elmospa.com/", body=r.STATUS_PAGE, status=200)
    client = ElmoClient(base_url=ELMO_E_CONNECT, domain="default")
    # Test
    client.auth("test", "test")
    assert len(server.calls) == 2
    request_body = dict(item.split("=") for item in server.calls[1].request.body.split("&"))
    assert client._session_id == "f8h23b4e-7a9f-4d3f-9b08-2769263ee33c"
    assert request_body == {
        "IsDisableAccountCreation": "True",
        "IsAllowThemeChange": "True",
        "UserName": "test",
        "Password": "test",
        "RememberMe": "false",
    }


def test_client_auth_econnect_web_login_metronet(server):
    """Web login must be used when accessing with Metronet.
    Regression test: https://github.com/palazzem/econnect-python/issues/186
    """
    server.add(responses.GET, "https://metronet.iessonline.com/api/login", body=r.LOGIN, status=200)
    server.add(responses.POST, "https://metronet.iessonline.com/domain", body=r.STATUS_PAGE, status=200)
    client = ElmoClient(base_url=IESS_METRONET, domain="domain")
    # Test
    client.auth("test", "test")
    assert len(server.calls) == 2
    request_body = dict(item.split("=") for item in server.calls[1].request.body.split("&"))
    assert client._session_id == "f8h23b4e-7a9f-4d3f-9b08-2769263ee33c"
    assert request_body == {
        "IsDisableAccountCreation": "True",
        "IsAllowThemeChange": "True",
        "UserName": "test",
        "Password": "test",
        "RememberMe": "false",
    }


def test_client_auth_metronet_web_login_with_default_domain(server):
    """Web login must be used when accessing with Metronet.
    Regression test: https://github.com/palazzem/econnect-python/issues/186
    """
    server.add(responses.GET, "https://metronet.iessonline.com/api/login", body=r.LOGIN, status=200)
    server.add(responses.POST, "https://metronet.iessonline.com/", body=r.STATUS_PAGE, status=200)
    client = ElmoClient(base_url=IESS_METRONET, domain="default")
    # Test
    client.auth("test", "test")
    assert len(server.calls) == 2
    request_body = dict(item.split("=") for item in server.calls[1].request.body.split("&"))
    assert client._session_id == "f8h23b4e-7a9f-4d3f-9b08-2769263ee33c"
    assert request_body == {
        "IsDisableAccountCreation": "True",
        "IsAllowThemeChange": "True",
        "UserName": "test",
        "Password": "test",
        "RememberMe": "false",
    }


def test_client_poll_with_changes(server):
    """Should return a dict with updated states."""
    html = """
        {
            "ConnectionStatus": false,
            "CanElevate": false,
            "LoggedIn": false,
            "LoginInProgress": false,
            "Areas": true,
            "Events": false,
            "Inputs": true,
            "Outputs": true,
            "Anomalies": false,
            "ReadStringsInProgress": false,
            "ReadStringPercentage": 0,
            "Strings": 0,
            "ManagedAccounts": false,
            "Temperature": false,
            "StatusAdv": true,
            "Images": false,
            "AdditionalInfoSupported": true,
            "HasChanges": true
        }
    """
    server.add(responses.POST, "https://example.com/api/updates", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    ids = {
        query.SECTORS: 42,
        query.INPUTS: 4242,
        query.OUTPUTS: 424,
        query.ALERTS: 424242,
    }
    # Test
    state = client.poll(ids)
    assert len(state.keys()) == 5
    assert state["has_changes"] is True
    assert state["inputs"] is True
    assert state["areas"] is True
    assert state["outputs"] is True
    assert state["statusadv"] is True


def test_client_poll_ignore_has_changes(server):
    """Should ignore HasChanges value to prevent `event` updates."""
    html = """
        {
            "ConnectionStatus": false,
            "CanElevate": false,
            "LoggedIn": false,
            "LoginInProgress": false,
            "Areas": false,
            "Events": true,
            "Inputs": false,
            "Outputs": false,
            "Anomalies": false,
            "ReadStringsInProgress": false,
            "ReadStringPercentage": 0,
            "Strings": 0,
            "ManagedAccounts": false,
            "Temperature": false,
            "StatusAdv": false,
            "Images": false,
            "AdditionalInfoSupported": true,
            "HasChanges": true
        }
    """
    server.add(responses.POST, "https://example.com/api/updates", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    ids = {
        query.SECTORS: 42,
        query.INPUTS: 4242,
        query.OUTPUTS: 424,
        query.ALERTS: 424242,
    }
    # Test
    state = client.poll(ids)
    assert len(state.keys()) == 5
    assert state["has_changes"] is False


def test_client_poll_unknown_error(server):
    """Should raise an Exception for unknown status code."""
    server.add(
        responses.POST,
        "https://example.com/api/updates",
        body="Server Error",
        status=500,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    ids = {
        query.SECTORS: 42,
        query.INPUTS: 4242,
        query.OUTPUTS: 424,
        query.ALERTS: 424242,
    }
    # Test
    with pytest.raises(HTTPError):
        client.poll(ids)
    assert len(server.calls) == 1


class TestClientPollParseError:
    def test_areas_missing(self, server):
        """Should raise a ParseError if the response is different from what is expected.
        In this case `Areas` is missing from the response."""
        html = """
            {
                "ConnectionStatus": false,
                "CanElevate": false,
                "LoggedIn": false,
                "LoginInProgress": false,
                "Events": true,
                "Inputs": false,
                "Outputs": false,
                "Anomalies": false,
                "ReadStringsInProgress": false,
                "ReadStringPercentage": 0,
                "Strings": 0,
                "ManagedAccounts": false,
                "Temperature": false,
                "StatusAdv": false,
                "Images": false,
                "AdditionalInfoSupported": true,
                "HasChanges": false
            }
        """
        server.add(responses.POST, "https://example.com/api/updates", body=html, status=200)
        client = ElmoClient(base_url="https://example.com", domain="domain")
        client._session_id = "test"
        ids = {
            query.SECTORS: 42,
            query.INPUTS: 4242,
            query.OUTPUTS: 424,
            query.ALERTS: 424242,
        }
        # Test
        with pytest.raises(ParseError):
            client.poll(ids)

    def test_inputs_missing(self, server):
        """Should raise a ParseError if the response is different from what is expected.
        In this case `Inputs` is missing from the response."""
        html = """
            {
                "ConnectionStatus": false,
                "CanElevate": false,
                "LoggedIn": false,
                "LoginInProgress": false,
                "Areas": false,
                "Events": true,
                "Outputs": false,
                "Anomalies": false,
                "ReadStringsInProgress": false,
                "ReadStringPercentage": 0,
                "Strings": 0,
                "ManagedAccounts": false,
                "Temperature": false,
                "StatusAdv": false,
                "Images": false,
                "AdditionalInfoSupported": true,
                "HasChanges": false
            }
        """
        server.add(responses.POST, "https://example.com/api/updates", body=html, status=200)
        client = ElmoClient(base_url="https://example.com", domain="domain")
        client._session_id = "test"
        ids = {
            query.SECTORS: 42,
            query.INPUTS: 4242,
            query.OUTPUTS: 424,
            query.ALERTS: 424242,
        }
        # Test
        with pytest.raises(ParseError):
            client.poll(ids)

    def test_outputs_missing(self, server):
        """Should raise a ParseError if the response is different from what is expected.
        In this case `Outputs` is missing from the response."""
        html = """
            {
                "ConnectionStatus": false,
                "CanElevate": false,
                "LoggedIn": false,
                "LoginInProgress": false,
                "Areas": false,
                "Events": true,
                "Inputs": false,
                "Anomalies": false,
                "ReadStringsInProgress": false,
                "ReadStringPercentage": 0,
                "Strings": 0,
                "ManagedAccounts": false,
                "Temperature": false,
                "StatusAdv": false,
                "Images": false,
                "AdditionalInfoSupported": true,
                "HasChanges": false
            }
        """
        server.add(responses.POST, "https://example.com/api/updates", body=html, status=200)
        client = ElmoClient(base_url="https://example.com", domain="domain")
        client._session_id = "test"
        ids = {
            query.SECTORS: 42,
            query.INPUTS: 4242,
            query.OUTPUTS: 424,
            query.ALERTS: 424242,
        }
        # Test
        with pytest.raises(ParseError):
            client.poll(ids)

    def test_statusadv_missing(self, server):
        """Should raise a ParseError if the response is different from what is expected.
        In this case `StatusAdv` is missing from the response."""
        html = """
            {
                "ConnectionStatus": false,
                "CanElevate": false,
                "LoggedIn": false,
                "LoginInProgress": false,
                "Areas": false,
                "Events": true,
                "Inputs": false,
                "Outputs": false,
                "Anomalies": false,
                "ReadStringsInProgress": false,
                "ReadStringPercentage": 0,
                "Strings": 0,
                "ManagedAccounts": false,
                "Temperature": false,
                "Images": false,
                "AdditionalInfoSupported": true,
                "HasChanges": false
            }
        """
        server.add(responses.POST, "https://example.com/api/updates", body=html, status=200)
        client = ElmoClient(base_url="https://example.com", domain="domain")
        client._session_id = "test"
        ids = {
            query.SECTORS: 42,
            query.INPUTS: 4242,
            query.OUTPUTS: 424,
            query.ALERTS: 424242,
        }
        # Test
        with pytest.raises(ParseError):
            client.poll(ids)


def test_client_lock(server, mocker):
    """Should acquire the lock, sending `userId=1` as a default."""
    html = """[
        {
            "Poller": {"Poller": 1, "Panel": 1},
            "CommandId": 5,
            "Successful": true
        }
    ]"""
    server.add(responses.POST, "https://example.com/api/panel/syncLogin", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    mocker.patch.object(client, "unlock")
    # Test
    with client.lock("test"):
        assert not client._lock.acquire(False)
    assert len(server.calls) == 1
    assert server.calls[0].request.body == "userId=1&password=test&sessionId=test"


def test_client_lock_with_user_id(server, mocker):
    """Should acquire the lock sending a user-defined `userId`."""
    html = """[
        {
            "Poller": {"Poller": 1, "Panel": 1},
            "CommandId": 5,
            "Successful": true
        }
    ]"""
    server.add(responses.POST, "https://example.com/api/panel/syncLogin", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    mocker.patch.object(client, "unlock")
    # Test
    with client.lock("test", user_id="001"):
        assert not client._lock.acquire(False)
    assert len(server.calls) == 1
    assert server.calls[0].request.body == "userId=001&password=test&sessionId=test"


def test_client_lock_wrong_code(server, mocker):
    """Should raise a CodeError if inserted code is not correct."""
    html = """[
        {
            "Poller": {"Poller": 1, "Panel": 1},
            "CommandId": 5,
            "Successful": false
        }
    ]"""
    server.add(responses.POST, "https://example.com/api/panel/syncLogin", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    mocker.patch.object(client, "unlock")
    # Test
    with pytest.raises(CodeError), client.lock("test"):
        pass
    assert len(server.calls) == 1


def test_client_lock_called_twice(server, mocker):
    """Should raise a CodeError if Lock() is called twice."""
    server.add(responses.POST, "https://example.com/api/panel/syncLogin", status=403)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    mocker.patch.object(client, "unlock")
    # Test
    with pytest.raises(LockError), client.lock("test"):
        pass
    assert len(server.calls) == 1


def test_client_lock_invalid_token(server, mocker):
    """Should raise a CodeError if the token is expired while calling Lock()."""
    server.add(responses.POST, "https://example.com/api/panel/syncLogin", status=401)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    mocker.patch.object(client, "unlock")
    # Test
    with pytest.raises(InvalidToken), client.lock("test"):
        pass
    assert len(server.calls) == 1


def test_client_lock_unknown_error(server, mocker):
    """Should raise an Exception for unknown status code."""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncLogin",
        body="Server Error",
        status=500,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    mocker.patch.object(client, "unlock")
    # Test
    with pytest.raises(HTTPError), client.lock(None):
        pass
    assert len(server.calls) == 1


def test_client_lock_calls_unlock(server, mocker):
    """Should call unlock() when exiting from the context."""
    html = """[
        {
            "Poller": {"Poller": 1, "Panel": 1},
            "CommandId": 5,
            "Successful": true
        }
    ]"""
    server.add(responses.POST, "https://example.com/api/panel/syncLogin", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    mocker.patch.object(client, "unlock")
    # Test
    with client.lock("test"):
        pass
    assert client.unlock.called is True
    assert len(server.calls) == 1


def test_client_lock_and_unlock_with_exception(server, mocker):
    """Should call unlock() even if an exception is raised in the block."""
    html = """[
        {
            "Poller": {"Poller": 1, "Panel": 1},
            "CommandId": 5,
            "Successful": true
        }
    ]"""
    server.add(responses.POST, "https://example.com/api/panel/syncLogin", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    mocker.patch.object(client, "unlock")
    # Test
    with pytest.raises(Exception), client.lock("test"):
        raise Exception
    assert client.unlock.called is True
    assert len(server.calls) == 1


def test_client_unlock(server):
    """Should call the API and release the system lock."""
    html = """[
        {
            "Poller": {"Poller": 1, "Panel": 1},
            "CommandId": 5,
            "Successful": true
        }
    ]"""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncLogout",
        body=html,
        status=200,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._lock.acquire()
    # Test
    assert client.unlock() is True
    assert client._lock.acquire(False)
    assert len(server.calls) == 1


def test_client_unlock_fails_missing_lock(server):
    """unlock() should fail without calling the endpoint if Lock() has not been acquired."""
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    # Test
    with pytest.raises(LockNotAcquired):
        client.unlock()
    assert client._lock.acquire(False)
    assert len(server.calls) == 0


def test_client_unlock_fails_forbidden(server):
    """Should fail if wrong credentials are used."""
    html = """[
        {
            "Poller": {"Poller": 1, "Panel": 1},
            "CommandId": 5,
            "Successful": false
        }
    ]"""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncLogout",
        body=html,
        status=403,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._lock.acquire()
    # Test
    with pytest.raises(LockNotAcquired):
        client.unlock()
    assert not client._lock.locked()
    assert len(server.calls) == 1


def test_client_unlock_fails_unexpected_error(server):
    """Should raise an error and keep the lock if the server has problems."""
    html = """[
        {
            "Poller": {"Poller": 1, "Panel": 1},
            "CommandId": 5,
            "Successful": false
        }
    ]"""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncLogout",
        body=html,
        status=500,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._lock.acquire()
    # Test
    with pytest.raises(HTTPError):
        client.unlock()
    assert not client._lock.acquire(False)
    assert len(server.calls) == 1


def test_client_arm(server):
    """Should call the API and arm the system."""
    html = """[
        {
            "Poller": {"Poller": 1, "Panel": 1},
            "CommandId": 5,
            "Successful": true
        }
    ]"""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncSendCommand",
        body=html,
        status=200,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._lock.acquire()
    # Test
    assert client.arm() is True
    assert len(server.calls) == 1
    body = server.calls[0].request.body.split("&")
    assert "CommandType=1" in body
    assert "ElementsClass=1" in body
    assert "ElementsIndexes=1" in body
    assert "sessionId=test" in body


def test_client_arm_single_sector(server):
    """Should call the API and arm only the given sector."""
    html = """[
        {
            "Poller": {"Poller": 1, "Panel": 1},
            "CommandId": 5,
            "Successful": true
        }
    ]"""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncSendCommand",
        body=html,
        status=200,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._lock.acquire()
    # Test
    assert client.arm([3]) is True
    assert len(server.calls) == 1
    body = server.calls[0].request.body.split("&")
    assert "CommandType=1" in body
    assert "ElementsClass=9" in body
    assert "ElementsIndexes=3" in body
    assert "sessionId=test" in body


def test_client_arm_multiple_sectors(server):
    """Should call the API and arm only the given sectors."""
    html = """[
        {
            "Poller": {"Poller": 1, "Panel": 1},
            "CommandId": 5,
            "Successful": true
        }
    ]"""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncSendCommand",
        body=html,
        status=200,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._lock.acquire()
    # Test
    assert client.arm([3, 4]) is True
    assert len(server.calls) == 1
    body = server.calls[0].request.body.split("&")
    assert "CommandType=1" in body
    assert "ElementsClass=9" in body
    assert "ElementsIndexes=3" in body
    assert "ElementsIndexes=4" in body
    assert "sessionId=test" in body


def test_client_arm_fails_missing_lock(server):
    """arm() should fail without calling the endpoint if Lock() has not been acquired."""
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    # Test
    with pytest.raises(LockNotAcquired):
        client.arm()
    assert client._lock.acquire(False)
    assert len(server.calls) == 0


def test_client_arm_fails_missing_session(server):
    """Should fail if a wrong access token is used."""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncSendCommand",
        status=401,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._lock.acquire()
    # Test
    with pytest.raises(InvalidToken):
        client.arm()
    assert len(server.calls) == 1


def test_client_arm_fails_wrong_sector(server):
    """Should fail if a not existing sector is used."""
    html = """[
        {
            "Poller": {"Poller": 1, "Panel": 1},
            "CommandId": 5,
            "Successful": false
        }
    ]"""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncSendCommand",
        body=html,
        status=200,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._lock.acquire()
    # Test
    with pytest.raises(CommandError):
        assert client.arm([200])


def test_client_arm_fails_unknown_error(server):
    """Should fail if an unknown error happens."""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncSendCommand",
        body="Server Error",
        status=500,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._lock.acquire()
    # Test
    with pytest.raises(HTTPError):
        client.arm()
    assert len(server.calls) == 1


def test_client_disarm(server):
    """Should call the API and disarm the system."""
    html = """[
        {
            "Poller": {"Poller": 1, "Panel": 1},
            "CommandId": 5,
            "Successful": true
        }
    ]"""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncSendCommand",
        body=html,
        status=200,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._lock.acquire()
    # Test
    assert client.disarm() is True
    assert len(server.calls) == 1
    body = server.calls[0].request.body.split("&")
    assert "CommandType=2" in body
    assert "ElementsClass=1" in body
    assert "ElementsIndexes=1" in body
    assert "sessionId=test" in body


def test_client_disarm_single_sector(server):
    """Should call the API and disarm only the given sector."""
    html = """[
        {
            "Poller": {"Poller": 1, "Panel": 1},
            "CommandId": 5,
            "Successful": true
        }
    ]"""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncSendCommand",
        body=html,
        status=200,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._lock.acquire()
    # Test
    assert client.disarm([3]) is True
    assert len(server.calls) == 1
    body = server.calls[0].request.body.split("&")
    assert "CommandType=2" in body
    assert "ElementsClass=9" in body
    assert "ElementsIndexes=3" in body
    assert "sessionId=test" in body


def test_client_disarm_multiple_sectors(server):
    """Should call the API and disarm only the given sectors."""
    html = """[
        {
            "Poller": {"Poller": 1, "Panel": 1},
            "CommandId": 5,
            "Successful": true
        }
    ]"""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncSendCommand",
        body=html,
        status=200,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._lock.acquire()
    # Test
    assert client.disarm([3, 4]) is True
    assert len(server.calls) == 1
    body = server.calls[0].request.body.split("&")
    assert "CommandType=2" in body
    assert "ElementsClass=9" in body
    assert "ElementsIndexes=3" in body
    assert "ElementsIndexes=4" in body
    assert "sessionId=test" in body


def test_client_disarm_fails_missing_lock(server):
    """disarm() should fail without calling the endpoint if Lock() has not been acquired."""
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    # Test
    with pytest.raises(LockNotAcquired):
        client.disarm()
    assert client._lock.acquire(False)
    assert len(server.calls) == 0


def test_client_disarm_fails_missing_session(server):
    """Should fail if a wrong access token is used."""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncSendCommand",
        status=401,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._lock.acquire()
    # Test
    with pytest.raises(InvalidToken):
        client.disarm()
    assert len(server.calls) == 1


def test_client_disarm_fails_wrong_sector(server):
    """Should fail if a not existing sector is used."""
    html = """[
        {
            "Poller": {"Poller": 1, "Panel": 1},
            "CommandId": 5,
            "Successful": false
        }
    ]"""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncSendCommand",
        body=html,
        status=200,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._lock.acquire()
    # Test
    with pytest.raises(CommandError):
        assert client.disarm([200])


def test_client_disarm_fails_unknown_error(server):
    """Should fail if an unknown error happens."""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncSendCommand",
        body="Server Error",
        status=500,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "unknown"
    client._lock.acquire()
    # Test
    with pytest.raises(HTTPError):
        client.disarm()
    assert len(server.calls) == 1


def test_client_include(server):
    """Should call the API and include the given input."""
    html = """[
        {
            "Poller": {"Poller": 1, "Panel": 1},
            "CommandId": 147,
            "Successful": true,
            "ErrorMessages": []
        }
    ]"""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncSendCommand",
        body=html,
        status=200,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._lock.acquire()
    # Test
    assert client.include([3]) is True
    assert len(server.calls) == 1
    body = server.calls[0].request.body.split("&")
    assert "CommandType=1" in body
    assert "ElementsClass=10" in body
    assert "ElementsIndexes=3" in body
    assert "sessionId=test" in body


def test_client_include_multiple_inputs(server):
    """Should call the API and include given inputs."""
    html = """[
        {
            "Poller": {"Poller": 1, "Panel": 1},
            "CommandId": 147,
            "Successful": true,
            "ErrorMessages": []
        }
    ]"""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncSendCommand",
        body=html,
        status=200,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._lock.acquire()
    # Test
    assert client.include([3, 4]) is True
    assert len(server.calls) == 2
    body = server.calls[0].request.body.split("&")
    assert "CommandType=1" in body
    assert "ElementsClass=10" in body
    assert "ElementsIndexes=3" in body
    assert "sessionId=test" in body
    body = server.calls[1].request.body.split("&")
    assert "CommandType=1" in body
    assert "ElementsClass=10" in body
    assert "ElementsIndexes=4" in body
    assert "sessionId=test" in body


def test_client_include_fails_missing_lock(server):
    """include() should fail without calling the endpoint if Lock() has not been acquired."""
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    # Test
    with pytest.raises(LockNotAcquired):
        client.include([1])
    assert client._lock.acquire(False)
    assert len(server.calls) == 0


def test_client_include_fails_missing_session(server):
    """Should fail if a wrong access token is used."""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncSendCommand",
        status=401,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._lock.acquire()
    # Test
    with pytest.raises(InvalidToken):
        client.include([1])
    assert len(server.calls) == 1


def test_client_include_fails_wrong_input(server):
    """Should fail if a not existing input is used."""
    html = """[
        {
            "Poller": {"Poller": 1, "Panel": 1},
            "CommandId": 147,
            "Successful": false,
            "ErrorMessages": ["Command failed."]
        }
    ]"""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncSendCommand",
        body=html,
        status=200,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._lock.acquire()
    # Test
    with pytest.raises(CommandError):
        assert client.include([9000])


def test_client_include_fails_unknown_error(server):
    """Should fail if an unknown error happens."""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncSendCommand",
        body="Server Error",
        status=500,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._lock.acquire()
    # Test
    with pytest.raises(HTTPError):
        client.include([1])
    assert len(server.calls) == 1


def test_client_exclude(server):
    """Should call the API and exclude only the given inputs."""
    html = """[
        {
            "Poller": {"Poller": 1, "Panel": 1},
            "CommandId": 147,
            "Successful": true,
            "ErrorMessages": []
        }
    ]"""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncSendCommand",
        body=html,
        status=200,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._lock.acquire()
    # Test
    assert client.exclude([3]) is True
    assert len(server.calls) == 1
    body = server.calls[0].request.body.split("&")
    assert "CommandType=2" in body
    assert "ElementsClass=10" in body
    assert "ElementsIndexes=3" in body
    assert "sessionId=test" in body


def est_client_exclude_multiple_inputs(server):
    """Should call the API and exclude only the given inputs."""
    html = """[
        {
            "Poller": {"Poller": 1, "Panel": 1},
            "CommandId": 147,
            "Successful": true,
            "ErrorMessages": []
        }
    ]"""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncSendCommand",
        body=html,
        status=200,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._lock.acquire()
    # Test
    assert client.exclude([3, 4]) is True
    assert len(server.calls) == 2
    body = server.calls[0].request.body.split("&")
    assert "CommandType=2" in body
    assert "ElementsClass=10" in body
    assert "ElementsIndexes=3" in body
    assert "sessionId=test" in body
    body = server.calls[1].request.body.split("&")
    assert "CommandType=2" in body
    assert "ElementsClass=10" in body
    assert "ElementsIndexes=4" in body
    assert "sessionId=test" in body


def test_client_exclude_fails_missing_lock(server):
    """exclude() should fail without calling the endpoint if Lock() has not been acquired."""
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    # Test
    with pytest.raises(LockNotAcquired):
        client.exclude([1])
    assert client._lock.acquire(False)
    assert len(server.calls) == 0


def test_client_exclude_fails_missing_session(server):
    """Should fail if a wrong access token is used."""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncSendCommand",
        status=401,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._lock.acquire()
    # Test
    with pytest.raises(InvalidToken):
        client.exclude([1])
    assert len(server.calls) == 1


def test_client_exclude_fails_wrong_input(server):
    """Should fail if a not existing input is used."""
    html = """[
        {
            "Poller": {"Poller": 1, "Panel": 1},
            "CommandId": 147,
            "Successful": false,
            "ErrorMessages": ["Command failed."]
        }
    ]"""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncSendCommand",
        body=html,
        status=200,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._lock.acquire()
    # Test
    with pytest.raises(CommandError):
        assert client.exclude([9000])


def test_client_exclude_fails_unknown_error(server):
    """Should fail if an unknown error happens."""
    server.add(
        responses.POST,
        "https://example.com/api/panel/syncSendCommand",
        body="Server Error",
        status=500,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "unknown"
    client._lock.acquire()
    # Test
    with pytest.raises(HTTPError):
        client.exclude([1])
    assert len(server.calls) == 1


class TestTurnOn:
    def test_client_single_output(self, server):
        """Should call the API and activate given output."""
        html = """[
            {
                "Poller": {"Poller": 1, "Panel": 1},
                "CommandId": 147,
                "Successful": true,
                "ErrorMessages": []
            }
        ]"""
        server.add(
            responses.POST,
            "https://example.com/api/panel/syncSendCommand",
            body=html,
            status=200,
        )
        client = ElmoClient(base_url="https://example.com", domain="domain")
        client._session_id = "test"
        # Test
        assert client.turn_on([3]) is True
        assert len(server.calls) == 1
        body = server.calls[0].request.body.split("&")
        assert "CommandType=1" in body
        assert "ElementsClass=12" in body
        assert "ElementsIndexes=3" in body
        assert "sessionId=test" in body

    def test_client_multiple_outputs(self, server):
        """Should call the API and activate given outputs."""
        html = """[
            {
                "Poller": {"Poller": 1, "Panel": 1},
                "CommandId": 147,
                "Successful": true,
                "ErrorMessages": []
            }
        ]"""
        server.add(
            responses.POST,
            "https://example.com/api/panel/syncSendCommand",
            body=html,
            status=200,
        )
        client = ElmoClient(base_url="https://example.com", domain="domain")
        client._session_id = "test"
        # Test
        assert client.turn_on([3, 4]) is True
        assert len(server.calls) == 1
        body = server.calls[0].request.body.split("&")
        assert "CommandType=1" in body
        assert "ElementsClass=12" in body
        assert "ElementsIndexes=3" in body
        assert "ElementsIndexes=4" in body
        assert "sessionId=test" in body

    def test_client_fails_missing_session(self, server):
        """Should fail if a wrong access token is used."""
        server.add(
            responses.POST,
            "https://example.com/api/panel/syncSendCommand",
            status=401,
        )
        client = ElmoClient(base_url="https://example.com", domain="domain")
        client._session_id = "test"
        client._lock.acquire()
        # Test
        with pytest.raises(InvalidToken):
            client.turn_on([1])
        assert len(server.calls) == 1

    def test_client_fails_wrong_input(self, server):
        """Should fail if a not existing output is used."""
        html = """[
            {
                "Poller": {"Poller": 1, "Panel": 1},
                "CommandId": 147,
                "Successful": false,
                "ErrorMessages": ["Command failed."]
            }
        ]"""
        server.add(
            responses.POST,
            "https://example.com/api/panel/syncSendCommand",
            body=html,
            status=200,
        )
        client = ElmoClient(base_url="https://example.com", domain="domain")
        client._session_id = "test"
        # Test
        with pytest.raises(CommandError):
            assert client.turn_on([9000])

    def test_client_fails_unknown_error(self, server):
        """Should fail if an unknown error happens."""
        server.add(
            responses.POST,
            "https://example.com/api/panel/syncSendCommand",
            body="Server Error",
            status=500,
        )
        client = ElmoClient(base_url="https://example.com", domain="domain")
        client._session_id = "test"
        # Test
        with pytest.raises(HTTPError):
            client.turn_on([1])
        assert len(server.calls) == 1


class TestTurnOff:
    def test_client_single_output(self, server):
        """Should call the API and deactivate given output."""
        html = """[
            {
                "Poller": {"Poller": 1, "Panel": 1},
                "CommandId": 147,
                "Successful": true,
                "ErrorMessages": []
            }
        ]"""
        server.add(
            responses.POST,
            "https://example.com/api/panel/syncSendCommand",
            body=html,
            status=200,
        )
        client = ElmoClient(base_url="https://example.com", domain="domain")
        client._session_id = "test"
        # Test
        assert client.turn_off([3]) is True
        assert len(server.calls) == 1
        body = server.calls[0].request.body.split("&")
        assert "CommandType=2" in body
        assert "ElementsClass=12" in body
        assert "ElementsIndexes=3" in body
        assert "sessionId=test" in body

    def test_client_multiple_outputs(self, server):
        """Should call the API and deactivate given outputs."""
        html = """[
            {
                "Poller": {"Poller": 1, "Panel": 1},
                "CommandId": 147,
                "Successful": true,
                "ErrorMessages": []
            }
        ]"""
        server.add(
            responses.POST,
            "https://example.com/api/panel/syncSendCommand",
            body=html,
            status=200,
        )
        client = ElmoClient(base_url="https://example.com", domain="domain")
        client._session_id = "test"
        # Test
        assert client.turn_off([3, 4]) is True
        assert len(server.calls) == 1
        body = server.calls[0].request.body.split("&")
        assert "CommandType=2" in body
        assert "ElementsClass=12" in body
        assert "ElementsIndexes=3" in body
        assert "ElementsIndexes=4" in body
        assert "sessionId=test" in body

    def test_client_fails_missing_session(self, server):
        """Should fail if a wrong access token is used."""
        server.add(
            responses.POST,
            "https://example.com/api/panel/syncSendCommand",
            status=401,
        )
        client = ElmoClient(base_url="https://example.com", domain="domain")
        client._session_id = "test"
        client._lock.acquire()
        # Test
        with pytest.raises(InvalidToken):
            client.turn_off([1])
        assert len(server.calls) == 1

    def test_client_fails_wrong_input(self, server):
        """Should fail if a not existing output is used."""
        html = """[
            {
                "Poller": {"Poller": 1, "Panel": 1},
                "CommandId": 147,
                "Successful": false,
                "ErrorMessages": ["Command failed."]
            }
        ]"""
        server.add(
            responses.POST,
            "https://example.com/api/panel/syncSendCommand",
            body=html,
            status=200,
        )
        client = ElmoClient(base_url="https://example.com", domain="domain")
        client._session_id = "test"
        # Test
        with pytest.raises(CommandError):
            assert client.turn_off([9000])

    def test_client_fails_unknown_error(self, server):
        """Should fail if an unknown error happens."""
        server.add(
            responses.POST,
            "https://example.com/api/panel/syncSendCommand",
            body="Server Error",
            status=500,
        )
        client = ElmoClient(base_url="https://example.com", domain="domain")
        client._session_id = "test"
        # Test
        with pytest.raises(HTTPError):
            client.turn_off([1])
        assert len(server.calls) == 1


def test_client_get_descriptions(server):
    """Should retrieve inputs/sectors descriptions."""
    html = """
    [
      {
        "AccountId": 1,
        "Class": 9,
        "Index": 0,
        "Description": "S1 Living Room",
        "Created": "/Date(1546004120767+0100)/",
        "Version": "AAAAAAAAgPc="
      },
      {
        "AccountId": 1,
        "Class": 9,
        "Index": 1,
        "Description": "S2 Bedroom",
        "Created": "/Date(1546004120770+0100)/",
        "Version": "AAAAAAAAgPg="
      },
      {
        "AccountId": 1,
        "Class": 10,
        "Index": 0,
        "Description": "Alarm",
        "Created": "/Date(1546004147490+0100)/",
        "Version": "AAAAAAAAgRs="
      },
      {
        "AccountId": 1,
        "Class": 10,
        "Index": 1,
        "Description": "Entryway Sensor",
        "Created": "/Date(1546004147493+0100)/",
        "Version": "AAAAAAAAgRw="
      }
    ]
    """
    server.add(responses.POST, "https://example.com/api/strings", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    # Test
    descriptions = client._get_descriptions()
    # Expected output
    assert len(server.calls) == 1
    assert descriptions == {
        9: {0: "S1 Living Room", 1: "S2 Bedroom"},
        10: {0: "Alarm", 1: "Entryway Sensor"},
    }
    # Check constants used in the code
    assert descriptions[query.SECTORS][0] == "S1 Living Room"
    assert descriptions[query.INPUTS][0] == "Alarm"


def test_client_get_descriptions_cached(server):
    """Should cache the result of get_descriptions()."""
    html = """
    [
      {
        "AccountId": 1,
        "Class": 9,
        "Index": 0,
        "Description": "S1 Living Room",
        "Created": "/Date(1546004120767+0100)/",
        "Version": "AAAAAAAAgPc="
      }
    ]
    """
    server.add(responses.POST, "https://example.com/api/strings", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    # Test
    client._get_descriptions()
    client._get_descriptions()
    assert len(server.calls) == 1


def test_client_get_descriptions_cache_releases_client(server):
    """Should not keep a discarded client alive through the descriptions cache."""
    server.add(responses.POST, "https://example.com/api/strings", body=r.STRINGS, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._get_descriptions()
    ref = weakref.ref(client)
    # Test
    del client
    gc.collect()
    assert ref() is None


def test_client_get_descriptions_unauthorized(server):
    """Should raise HTTPError if the request is unauthorized."""
    server.add(
        responses.POST,
        "https://example.com/api/strings",
        body="User not authenticated",
        status=403,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    # Test
    with pytest.raises(HTTPError):
        client._get_descriptions()


def test_client_get_descriptions_error(server):
    """Should raise HTTPError if there is a client error."""
    server.add(
        responses.POST,
        "https://example.com/api/strings",
        body="Bad Request",
        status=400,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    # Test
    with pytest.raises(HTTPError):
        client._get_descriptions()


def test_client_query_panel_details(panel_details):
    """Should query the system to retrieve panel details."""
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._panel = panel_details
    # Test
    details = client.query(query.PANEL)
    # Expected output
    assert details == {
        "last_id": 0,
        "panel": {
            "description": "T-800 1.0.1",
            "last_connection": "01/01/1984 13:27:28",
            "last_disconnection": "01/10/1984 13:27:18",
            "major": 1,
            "minor": 0,
            "source_ip": "10.0.0.1",
            "connection_type": "EthernetWiFi",
            "device_class": 92,
            "revision": 1,
            "build": 1,
            "brand": 0,
            "language": 0,
            "areas": 4,
            "sectors_per_area": 4,
            "total_sectors": 16,
            "inputs": 24,
            "outputs": 24,
            "operators": 64,
            "sectors_in_use": [
                True,
                True,
                True,
                True,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
            ],
            "model": "T-800",
            "login_without_user_id": True,
            "additional_info_supported": 1,
            "is_fire_panel": False,
        },
    }


def test_client_query_panel_details_empty():
    """Should return an empty dict if the login has not been completed."""
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    # Test
    details = client.query(query.PANEL)
    # Expected output
    assert details == {
        "last_id": 0,
        "panel": {},
    }


def test_client_query_panel_details_deep_copy(panel_details):
    """Should return a deep copy."""
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    client._panel = panel_details
    # Test
    details = client.query(query.PANEL)
    # Expected output
    assert details["panel"] is not client._panel


def test_client_get_sectors_status(server, mocker):
    """Should query a Elmo system to retrieve sectors status."""
    html = """[
       {
           "Active": true,
           "ActivePartial": false,
           "Max": false,
           "Activable": true,
           "ActivablePartial": false,
           "InUse": true,
           "Id": 1,
           "Index": 0,
           "Element": 1,
           "CommandId": 0,
           "InProgress": false
       },
       {
           "Active": true,
           "ActivePartial": false,
           "Max": false,
           "Activable": true,
           "ActivablePartial": false,
           "InUse": true,
           "Id": 2,
           "Index": 1,
           "Element": 2,
           "CommandId": 0,
           "InProgress": false
       },
       {
           "Active": false,
           "ActivePartial": false,
           "Max": false,
           "Activable": false,
           "ActivablePartial": false,
           "InUse": true,
           "Id": 3,
           "Index": 2,
           "Element": 3,
           "CommandId": 0,
           "InProgress": false
       },
       {
           "Active": false,
           "ActivePartial": false,
           "Max": false,
           "Activable": true,
           "ActivablePartial": false,
           "InUse": false,
           "Id": 4,
           "Index": 3,
           "Element": 5,
           "CommandId": 0,
           "InProgress": false
       }
    ]"""
    # query() depends on _get_descriptions()
    server.add(responses.POST, "https://example.com/api/areas", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    mocker.patch.object(client, "_get_descriptions")
    client._get_descriptions.return_value = {
        9: {0: "Living Room", 1: "Bedroom", 2: "Kitchen", 3: "Entryway"},
    }
    # Test
    sectors = client.query(query.SECTORS)
    # Expected output
    assert client._get_descriptions.called is True
    assert len(server.calls) == 1
    assert sectors == {
        "last_id": 4,
        "sectors": {
            0: {
                "element": 1,
                "id": 1,
                "index": 0,
                "status": True,
                "activable": True,
                "name": "Living Room",
            },
            1: {
                "element": 2,
                "id": 2,
                "index": 1,
                "status": True,
                "activable": True,
                "name": "Bedroom",
            },
            2: {
                "element": 3,
                "id": 3,
                "index": 2,
                "status": False,
                "activable": False,
                "name": "Kitchen",
            },
        },
    }


def test_client_get_inputs_status(server, mocker):
    """Should query a Elmo system to retrieve inputs status."""
    html = """[
       {
           "Alarm": true,
           "MemoryAlarm": false,
           "Excluded": false,
           "InUse": true,
           "IsVideo": false,
           "Id": 1,
           "Index": 0,
           "Element": 1,
           "CommandId": 0,
           "InProgress": false
       },
       {
           "Alarm": true,
           "MemoryAlarm": false,
           "Excluded": false,
           "InUse": true,
           "IsVideo": false,
           "Id": 2,
           "Index": 1,
           "Element": 2,
           "CommandId": 0,
           "InProgress": false
       },
       {
           "Alarm": false,
           "MemoryAlarm": false,
           "Excluded": true,
           "InUse": true,
           "IsVideo": false,
           "Id": 3,
           "Index": 2,
           "Element": 3,
           "CommandId": 0,
           "InProgress": false
       },
       {
           "Alarm": false,
           "MemoryAlarm": false,
           "Excluded": false,
           "InUse": false,
           "IsVideo": false,
           "Id": 4,
           "Index": 3,
           "Element": 4,
           "CommandId": 0,
           "InProgress": false
       }
    ]"""
    # query() depends on _get_descriptions()
    server.add(responses.POST, "https://example.com/api/inputs", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    mocker.patch.object(client, "_get_descriptions")
    client._get_descriptions.return_value = {
        10: {0: "Alarm", 1: "Window kitchen", 2: "Door entryway", 3: "Window bathroom"},
    }
    # Test
    inputs = client.query(query.INPUTS)
    # Expected output
    assert client._get_descriptions.called is True
    assert len(server.calls) == 1
    assert inputs == {
        "last_id": 4,
        "inputs": {
            0: {
                "element": 1,
                "id": 1,
                "index": 0,
                "status": True,
                "excluded": False,
                "name": "Alarm",
            },
            1: {
                "element": 2,
                "id": 2,
                "index": 1,
                "status": True,
                "excluded": False,
                "name": "Window kitchen",
            },
            2: {
                "element": 3,
                "id": 3,
                "status": False,
                "index": 2,
                "excluded": True,
                "name": "Door entryway",
            },
        },
    }


def test_client_get_outputs_status(server, mocker):
    """Should query a Elmo system to retrieve outputs status."""
    html = """[
       {
        "Active": true,
        "InUse": true,
        "DoNotRequireAuthentication": true,
        "ControlDeniedToUsers": false,
        "Id": 400258,
        "Index": 0,
        "Element": 1,
        "CommandId": 0,
        "InProgress": false
    },
    {
        "Active": false,
        "InUse": true,
        "DoNotRequireAuthentication": false,
        "ControlDeniedToUsers": false,
        "Id": 400259,
        "Index": 1,
        "Element": 2,
        "CommandId": 0,
        "InProgress": false
    },
    {
        "Active": false,
        "InUse": true,
        "DoNotRequireAuthentication": false,
        "ControlDeniedToUsers": true,
        "Id": 400260,
        "Index": 2,
        "Element": 3,
        "CommandId": 0,
        "InProgress": false
    },
    {
        "Active": false,
        "InUse": false,
        "DoNotRequireAuthentication": false,
        "ControlDeniedToUsers": false,
        "Id": 400261,
        "Index": 3,
        "Element": 4,
        "CommandId": 0,
        "InProgress": false
    }
    ]"""
    # query() depends on _get_descriptions()
    server.add(responses.POST, "https://example.com/api/outputs", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    mocker.patch.object(client, "_get_descriptions")
    client._get_descriptions.return_value = {
        12: {0: "Output 1", 1: "Output 2", 2: "Output 3", 3: "Output 4"},
    }
    # Test
    outputs = client.query(query.OUTPUTS)
    # Expected output
    assert client._get_descriptions.called is True
    assert len(server.calls) == 1

    assert outputs == {
        "last_id": 400261,
        "outputs": {
            0: {
                "element": 1,
                "id": 400258,
                "index": 0,
                "status": True,
                "control_denied_to_users": False,
                "do_not_require_authentication": True,
                "name": "Output 1",
            },
            1: {
                "element": 2,
                "id": 400259,
                "index": 1,
                "status": False,
                "control_denied_to_users": False,
                "do_not_require_authentication": False,
                "name": "Output 2",
            },
            2: {
                "element": 3,
                "id": 400260,
                "status": False,
                "index": 2,
                "control_denied_to_users": True,
                "do_not_require_authentication": False,
                "name": "Output 3",
            },
        },
    }


def test_client_missing_sectors_strings(server, mocker):
    """The query should return an empty list if outputs strings are not synchronized.
    Regression test for: https://github.com/palazzem/ha-econnect-alarm/issues/115
    """
    html = """[
       {
           "Active": true,
           "ActivePartial": false,
           "Max": false,
           "Activable": true,
           "ActivablePartial": false,
           "InUse": true,
           "Id": 1,
           "Index": 0,
           "Element": 1,
           "CommandId": 0,
           "InProgress": false
       }
    ]"""
    server.add(responses.POST, "https://example.com/api/areas", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    mocker.patch.object(client, "_get_descriptions")
    client._get_descriptions.return_value = {}
    # Test
    sectors = client.query(query.SECTORS)
    # Expected output
    assert client._get_descriptions.called is True
    assert len(server.calls) == 1
    assert sectors == {
        "last_id": 1,
        "sectors": {
            0: {
                "element": 1,
                "id": 1,
                "index": 0,
                "status": True,
                "activable": True,
                "name": "Unknown",
            },
        },
    }


def test_client_missing_inputs_strings(server, mocker):
    """The query should return an empty list if outputs strings are not synchronized.
    Regression test for: https://github.com/palazzem/ha-econnect-alarm/issues/115
    """
    html = """[
       {
           "Alarm": true,
           "MemoryAlarm": false,
           "Excluded": false,
           "InUse": true,
           "IsVideo": false,
           "Id": 1,
           "Index": 0,
           "Element": 1,
           "CommandId": 0,
           "InProgress": false
       }
    ]"""
    server.add(responses.POST, "https://example.com/api/inputs", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    mocker.patch.object(client, "_get_descriptions")
    client._get_descriptions.return_value = {}
    # Test
    inputs = client.query(query.INPUTS)
    # Expected output
    assert client._get_descriptions.called is True
    assert len(server.calls) == 1
    assert inputs == {
        "last_id": 1,
        "inputs": {
            0: {
                "element": 1,
                "id": 1,
                "index": 0,
                "status": True,
                "excluded": False,
                "name": "Unknown",
            },
        },
    }


def test_client_missing_outputs_strings(server, mocker):
    """The query should return an empty list if outputs strings are not synchronized.
    Regression test for: https://github.com/palazzem/ha-econnect-alarm/issues/115
    """
    html = """[
       {
        "Active": true,
        "InUse": true,
        "DoNotRequireAuthentication": true,
        "ControlDeniedToUsers": false,
        "Id": 400258,
        "Index": 0,
        "Element": 1,
        "CommandId": 0,
        "InProgress": false
    }
    ]"""
    server.add(responses.POST, "https://example.com/api/outputs", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    mocker.patch.object(client, "_get_descriptions")
    client._get_descriptions.return_value = {}
    # Test
    outputs = client.query(query.OUTPUTS)
    # Expected output
    assert client._get_descriptions.called is True
    assert len(server.calls) == 1

    assert outputs == {
        "last_id": 400258,
        "outputs": {
            0: {
                "control_denied_to_users": False,
                "do_not_require_authentication": True,
                "element": 1,
                "id": 400258,
                "index": 0,
                "name": "Unknown",
                "status": True,
            },
        },
    }


def test_client_get_sectors_missing_area(server, mocker):
    """Should set an Unknown `sector` name if the description is missing.
    Regression test for: https://github.com/palazzem/econnect-python/issues/91"""
    html = """[
       {
           "Active": true,
           "ActivePartial": false,
           "Max": false,
           "Activable": true,
           "ActivablePartial": false,
           "InUse": true,
           "Id": 1,
           "Index": 0,
           "Element": 1,
           "CommandId": 0,
           "InProgress": false
       },
       {
           "Active": true,
           "ActivePartial": false,
           "Max": false,
           "Activable": true,
           "ActivablePartial": false,
           "InUse": true,
           "Id": 2,
           "Index": 1,
           "Element": 2,
           "CommandId": 0,
           "InProgress": false
       }
    ]"""
    server.add(responses.POST, "https://example.com/api/areas", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    mocker.patch.object(client, "_get_descriptions")
    client._get_descriptions.return_value = {
        9: {0: "Living Room"},
    }
    # Test
    sectors = client.query(query.SECTORS)
    assert sectors == {
        "last_id": 2,
        "sectors": {
            0: {
                "element": 1,
                "id": 1,
                "index": 0,
                "status": True,
                "activable": True,
                "name": "Living Room",
            },
            1: {
                "element": 2,
                "id": 2,
                "index": 1,
                "status": True,
                "activable": True,
                "name": "Unknown",
            },
        },
    }


def test_client_get_inputs_missing_area(server, mocker):
    """Should set an Unknown `input` name if the description is missing.
    Regression test for: https://github.com/palazzem/econnect-python/issues/91"""
    html = """[
       {
           "Alarm": true,
           "MemoryAlarm": false,
           "Excluded": false,
           "InUse": true,
           "IsVideo": false,
           "Id": 1,
           "Index": 0,
           "Element": 1,
           "CommandId": 0,
           "InProgress": false
       },
       {
           "Alarm": true,
           "MemoryAlarm": false,
           "Excluded": false,
           "InUse": true,
           "IsVideo": false,
           "Id": 2,
           "Index": 1,
           "Element": 2,
           "CommandId": 0,
           "InProgress": false
       }
    ]"""
    server.add(responses.POST, "https://example.com/api/inputs", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    mocker.patch.object(client, "_get_descriptions")
    client._get_descriptions.return_value = {
        10: {0: "Alarm"},
    }
    # Test
    inputs = client.query(query.INPUTS)
    assert inputs == {
        "last_id": 2,
        "inputs": {
            0: {
                "element": 1,
                "id": 1,
                "index": 0,
                "status": True,
                "excluded": False,
                "name": "Alarm",
            },
            1: {
                "element": 2,
                "id": 2,
                "index": 1,
                "status": True,
                "excluded": False,
                "name": "Unknown",
            },
        },
    }


def test_client_query_not_valid(client):
    """Should raise QueryNotValid if the query is not recognized."""
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    # Test
    with pytest.raises(QueryNotValid):
        client.query("wrong_query")


def test_client_query_unauthorized(server, mocker):
    """Should raise HTTPError if the request is unauthorized."""
    server.add(
        responses.POST,
        "https://example.com/api/areas",
        body="User not authenticated",
        status=403,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    mocker.patch.object(client, "_get_descriptions")
    # Test
    with pytest.raises(HTTPError):
        client.query(query.SECTORS)


def test_client_query_error(server, mocker):
    """Should raise HTTPError if there is a client error."""
    server.add(
        responses.POST,
        "https://example.com/api/areas",
        body="Bad Request",
        status=400,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    mocker.patch.object(client, "_get_descriptions")
    # Test
    with pytest.raises(HTTPError):
        client.query(query.SECTORS)


def test_client_query_invalid_response(server, mocker):
    """Should raise ParseError if the response doesn't pass the expected parsing."""
    html = """[
       {
           "Active": true,
           "ActivePartial": false,
           "Max": false,
           "Activable": true,
           "ActivablePartial": false,
           "Id": 1,
           "Index": 0,
           "Element": 1,
           "CommandId": 0,
           "InProgress": false
       }
    ]"""
    server.add(responses.POST, "https://example.com/api/areas", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    mocker.patch.object(client, "_get_descriptions")
    # Test
    with pytest.raises(ParseError):
        client.query(query.SECTORS)


def test_client_query_unit_disconnected(server, mocker):
    # Ensure that the client catches and raises an exception when the unit is disconnected
    server.add(
        responses.POST,
        "https://example.com/api/areas",
        body='"Centrale non connessa"',
        status=403,
    )
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    mocker.patch.object(client, "_get_descriptions")
    # Test
    with pytest.raises(DeviceDisconnectedError):
        client.query(query.SECTORS)


def test_client_get_alerts_status(server):
    """Should query a Elmo system to retrieve alerts status."""
    html = """
        {
            "StatusUid": 1,
            "PanelLeds": {
                "InputsLed": 2,
                "AnomaliesLed": 1,
                "AlarmLed": 0,
                "TamperLed": 0
            },
            "PanelAnomalies": {
                "HasAnomaly": false,
                "PanelTamper": 0,
                "PanelNoPower": 0,
                "PanelLowBattery": 0,
                "GsmAnomaly": 0,
                "GsmLowBalance": 0,
                "PstnAnomaly": 0,
                "SystemTest": 0,
                "ModuleRegistration": 0,
                "RfInterference": 0,
                "InputFailure": 0,
                "InputAlarm": 0,
                "InputBypass": 0,
                "InputLowBattery": 0,
                "InputNoSupervision": 0,
                "DeviceTamper": 0,
                "DeviceFailure": 0,
                "DeviceNoPower": 0,
                "DeviceLowBattery": 0,
                "DeviceNoSupervision": 0,
                "DeviceSystemBlock": 0
            },
            "PanelAlignmentAdv": {
                "ManualFwUpAvailable": false,
                "Id": 1,
                "Index": -1,
                "Element": 0
            }
        }
    """

    server.add(responses.POST, "https://example.com/api/statusadv", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    # Test
    alerts = client.query(query.ALERTS)
    body = server.calls[0].request.body
    assert body == "sessionId=test"
    # Expected output
    assert alerts == {
        "last_id": 1,
        "alerts": {
            0: {"name": "alarm_led", "status": 0},
            1: {"name": "anomalies_led", "status": 1},
            2: {"name": "device_failure", "status": 0},
            3: {"name": "device_low_battery", "status": 0},
            4: {"name": "device_no_power", "status": 0},
            5: {"name": "device_no_supervision", "status": 0},
            6: {"name": "device_system_block", "status": 0},
            7: {"name": "device_tamper", "status": 0},
            8: {"name": "gsm_anomaly", "status": 0},
            9: {"name": "gsm_low_balance", "status": 0},
            10: {"name": "has_anomaly", "status": False},
            11: {"name": "input_alarm", "status": 0},
            12: {"name": "input_bypass", "status": 0},
            13: {"name": "input_failure", "status": 0},
            14: {"name": "input_low_battery", "status": 0},
            15: {"name": "input_no_supervision", "status": 0},
            16: {"name": "inputs_led", "status": 2},
            17: {"name": "module_registration", "status": 0},
            18: {"name": "panel_low_battery", "status": 0},
            19: {"name": "panel_no_power", "status": 0},
            20: {"name": "panel_tamper", "status": 0},
            21: {"name": "pstn_anomaly", "status": 0},
            22: {"name": "rf_interference", "status": 0},
            23: {"name": "system_test", "status": 0},
            24: {"name": "tamper_led", "status": 0},
        },
    }


def test_client_get_alerts_http_error(server):
    """Should raise HTTPError if there is a client error."""
    server.add(responses.POST, "https://example.com/api/statusadv", body="500 Error", status=500)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    # Test
    with pytest.raises(HTTPError):
        client.query(query.ALERTS)
    assert len(server.calls) == 1


def test_client_get_alerts_invalid_json(server):
    """Should raise ParseError if the response is unexpected."""
    server.add(responses.POST, "https://example.com/api/statusadv", body="Invalid JSON", status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    # Test
    with pytest.raises(ParseError):
        client.query(query.ALERTS)
    assert len(server.calls) == 1


def test_client_get_alerts_missing_data(server):
    """Should raise ParseError if some response data is missing."""
    html = """
        {
            "StatusUid": 1,
            "PanelLeds": {
                "InputsLed": 2,
                "AnomaliesLed": 1,
                "AlarmLed": 0,
                "TamperLed": 0
            },
            "PanelAlignmentAdv": {
                "ManualFwUpAvailable": false,
                "Id": 1,
                "Index": -1,
                "Element": 0
            }
        }
    """
    server.add(responses.POST, "https://example.com/api/statusadv", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    # Test
    with pytest.raises(ParseError):
        client.query(query.ALERTS)
    assert len(server.calls) == 1


def test_client_query_last_id_unordered(server, mocker):
    """Should determine the last_id correctly even if entries are unordered.
    Regression test for: https://github.com/palazzem/econnect-python/issues/154
    """
    html = """[
       {
           "Alarm": true,
           "MemoryAlarm": false,
           "Excluded": false,
           "InUse": true,
           "IsVideo": false,
           "Id": 3,
           "Index": 0,
           "Element": 1,
           "CommandId": 0,
           "InProgress": false
       },
       {
           "Alarm": false,
           "MemoryAlarm": false,
           "Excluded": true,
           "InUse": true,
           "IsVideo": false,
           "Id": 5,
           "Index": 2,
           "Element": 3,
           "CommandId": 0,
           "InProgress": false
       },
       {
           "Alarm": true,
           "MemoryAlarm": false,
           "Excluded": false,
           "InUse": true,
           "IsVideo": false,
           "Id": 2,
           "Index": 1,
           "Element": 2,
           "CommandId": 0,
           "InProgress": false
       }
    ]"""
    server.add(responses.POST, "https://example.com/api/inputs", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    mocker.patch.object(client, "_get_descriptions")
    client._get_descriptions.return_value = {
        10: {0: "Input 1", 1: "Input 2", 2: "Input 3"},
    }
    # Test
    inputs = client.query(query.INPUTS)
    assert inputs["last_id"] == 5


def test_client_query_last_id_type_error(server, mocker):
    """Should default last_id to 0 if a TypeError occurs during max()."""
    html = """[
       {
           "Alarm": true,
           "InUse": true,
           "Id": "not-an-int",
           "Index": 0,
           "Element": 1
       },
       {
           "Alarm": false,
           "InUse": true,
           "Id": 2,
           "Index": 1,
           "Element": 2
       }
    ]"""
    server.add(responses.POST, "https://example.com/api/inputs", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    mocker.patch.object(client, "_get_descriptions")
    client._get_descriptions.return_value = {10: {0: "Input 1", 1: "Input 2"}}
    # Test
    inputs = client.query(query.INPUTS)
    assert inputs["last_id"] == 0


def test_client_query_last_id_value_error_empty(server, mocker):
    """Should default last_id to 0 if the entries list is empty (ValueError)."""
    html = """[]"""
    server.add(responses.POST, "https://example.com/api/inputs", body=html, status=200)
    client = ElmoClient(base_url="https://example.com", domain="domain")
    client._session_id = "test"
    mocker.patch.object(client, "_get_descriptions")
    client._get_descriptions.return_value = {}
    # Test
    inputs = client.query(query.INPUTS)
    assert inputs["last_id"] == 0
