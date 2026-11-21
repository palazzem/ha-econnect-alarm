import pytest
import responses

from custom_components.econnect_metronet.api.v1.client import ElmoClient
from tests.fixtures import responses as r


@pytest.fixture(scope="function")
def client():
    """Creates an instance of `ElmoClient` which emulates the behavior of a real client for
    testing purposes.

    Although this client instance operates with mocked calls, it is designed to function as
    if it were genuine. This ensures that the client's usage in tests accurately mirrors how it
    would be employed in real scenarios.

    Use it for integration tests where a realistic interaction with the `ElmoClient` is required
    without actual external calls.
    """
    client = ElmoClient(base_url="https://example.com", domain="domain")
    with responses.RequestsMock(assert_all_requests_are_fired=False) as server:
        server.add(responses.GET, "https://example.com/api/login", body=r.LOGIN, status=200)
        server.add(responses.POST, "https://example.com/api/updates", body=r.UPDATES, status=200)
        server.add(responses.POST, "https://example.com/api/panel/syncLogin", body=r.SYNC_LOGIN, status=200)
        server.add(responses.POST, "https://example.com/api/panel/syncLogout", body=r.SYNC_LOGOUT, status=200)
        server.add(
            responses.POST, "https://example.com/api/panel/syncSendCommand", body=r.SYNC_SEND_COMMAND, status=200
        )
        server.add(responses.POST, "https://example.com/api/strings", body=r.STRINGS, status=200)
        server.add(responses.POST, "https://example.com/api/areas", body=r.AREAS, status=200)
        server.add(responses.POST, "https://example.com/api/inputs", body=r.INPUTS, status=200)
        server.add(responses.POST, "https://example.com/api/outputs", body=r.OUTPUTS, status=200)
        yield client


@pytest.fixture(scope="function")
def panel_details():
    """Returns the panel details object."""
    return {
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


@pytest.fixture
def server():
    """Create a `responses` mock."""
    with responses.RequestsMock() as resp:
        yield resp
