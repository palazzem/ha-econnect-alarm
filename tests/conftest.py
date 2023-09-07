import pytest
import responses
from elmo.api.client import ElmoClient
from fixtures import responses as r

pytest_plugins = ["tests.hass.fixtures"]


@pytest.fixture
async def hass(hass):
    hass.data["custom_components"] = None
    yield hass


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
        yield client
