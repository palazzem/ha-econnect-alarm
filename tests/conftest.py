import pytest
import responses
from elmo.api.client import ElmoClient

from custom_components.econnect_metronet import async_setup
from custom_components.econnect_metronet.alarm_control_panel import EconnectAlarm
from custom_components.econnect_metronet.config_flow import EconnectConfigFlow
from custom_components.econnect_metronet.const import DOMAIN
from custom_components.econnect_metronet.coordinator import AlarmCoordinator
from custom_components.econnect_metronet.devices import AlarmDevice

from .fixtures import responses as r
from .helpers import MockConfigEntry

pytest_plugins = ["tests.hass.fixtures"]


@pytest.fixture
async def hass(hass):
    """Create a Home Assistant instance for testing.

    This fixture forces some settings to simulate a bootstrap process:
    - `custom_components` is reset to properly test the integration
    - `async_setup()` method is called
    """
    await async_setup(hass, {})
    hass.data["custom_components"] = None
    hass.data[DOMAIN]["test_entry_id"] = {}
    yield hass


@pytest.fixture(scope="function")
def alarm_device(client):
    """Yields an instance of AlarmDevice.

    This fixture provides a scoped instance of AlarmDevice initialized with
    the provided client.
    The device is connected and updated with mocked data

    Args:
        client: The client used to initialize the AlarmDevice.

    Yields:
        An instance of AlarmDevice.
    """
    device = AlarmDevice(client)
    device.connect("username", "password")
    device.update()
    yield device


@pytest.fixture(scope="function")
def panel(hass, config_entry, alarm_device, coordinator):
    """Fixture to provide a test instance of the EconnectAlarm entity.

    This sets up an AlarmDevice and its corresponding DataUpdateCoordinator,
    then initializes the EconnectAlarm entity with a test name and ID. It also
    assigns the Home Assistant instance and a mock entity ID to the created entity.

    Args:
        hass: Mock Home Assistant instance.
        client: Mock client for the AlarmDevice.

    Yields:
        EconnectAlarm: Initialized test instance of the EconnectAlarm entity.
    """
    entity = EconnectAlarm(unique_id="test_id", config=config_entry, device=alarm_device, coordinator=coordinator)
    entity.hass = hass
    return entity


@pytest.fixture(scope="function")
def coordinator(hass, config_entry, alarm_device):
    """Fixture to provide a test instance of the AlarmCoordinator.

    This sets up an AlarmDevice and its corresponding DataUpdateCoordinator.

    Args:
        hass: Mock Home Assistant instance.
        config_entry: Mock config entry.

    Yields:
        AlarmCoordinator: Initialized test instance of the AlarmCoordinator.
    """
    coordinator = AlarmCoordinator(hass, alarm_device, 5)
    # Override Configuration and Device with mocked versions
    coordinator.config_entry = config_entry
    coordinator._device._connection._session_id = "test_token"
    # Initializes the Coordinator to skip the first setup
    coordinator.data = {}
    yield coordinator


@pytest.fixture(scope="function")
def client(socket_enabled):
    """Creates an instance of `ElmoClient` which emulates the behavior of a real client for
    testing purposes.

    Although this client instance operates with mocked calls, it is designed to function as
    if it were genuine. This ensures that the client's usage in tests accurately mirrors how it
    would be employed in real scenarios.

    Use it for integration tests where a realistic interaction with the `ElmoClient` is required
    without actual external calls.

    NOTE: `socket_enabled` fixture from `pytest-socket` is required for this fixture to work. After
    a change in `responses` (https://github.com/getsentry/responses/pull/685) available from
    release 0.24.0 onwards, any call to `ElmoClient` indirectly create a dummy socket:

        >>> socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    forcing `pytest-socket` to fail with the following error:

        >>> pytest_socket.SocketBlockedError: A test tried to use socket.socket.

    Keep loading `socket_enabled` fixture until this issue is handled better in `responses` library.
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
        server.add(responses.POST, "https://example.com/api/statusadv", body=r.STATUS, status=200)
        yield client


@pytest.fixture(scope="function")
def config_entry():
    """Creates a mock config entry for testing purposes.

    This config entry is designed to emulate the behavior of a real config entry for
    testing purposes.
    """
    return MockConfigEntry(
        version=EconnectConfigFlow.VERSION,
        domain=DOMAIN,
        entry_id="test_entry_id",
        options={},
        data={
            "username": "test_user",
            "password": "test_password",
            "domain": "econnect_metronet",
            "system_base_url": "https://example.com",
        },
    )
