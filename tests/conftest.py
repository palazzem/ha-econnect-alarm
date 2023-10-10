import logging

import pytest
import responses
from elmo.api.client import ElmoClient
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.econnect_metronet.alarm_control_panel import EconnectAlarm
from custom_components.econnect_metronet.coordinator import AlarmCoordinator
from custom_components.econnect_metronet.devices import AlarmDevice

from .fixtures import responses as r

pytest_plugins = ["tests.hass.fixtures"]


@pytest.fixture
async def hass(hass):
    hass.data["custom_components"] = None
    yield hass


@pytest.fixture(scope="function")
def alarm_device(client):
    """Yields an instance of AlarmDevice.

    This fixture provides a scoped instance of AlarmDevice initialized with
    the provided client.

    Args:
        client: The client used to initialize the AlarmDevice.

    Yields:
        An instance of AlarmDevice.
    """
    device = AlarmDevice(client)
    yield device


@pytest.fixture(scope="function")
def alarm_entity(hass, client, config_entry):
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
    device = AlarmDevice(client)
    coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="econnect_metronet")
    entity = EconnectAlarm(unique_id="test_id", config=config_entry, device=device, coordinator=coordinator)
    entity.hass = hass
    yield entity


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
    coordinator = AlarmCoordinator(hass, config_entry)
    # Override Configuration and Device with mocked versions
    coordinator.config_entry = config_entry
    coordinator.device = alarm_device
    coordinator.device._connection._session_id = "test_token"
    yield coordinator


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
        server.add(responses.POST, "https://example.com/api/statusadv", body=r.STATUS, status=200)
        yield client


@pytest.fixture(scope="function")
def config_entry():
    """Creates a mock config entry for testing purposes.

    This config entry is designed to emulate the behavior of a real config entry for
    testing purposes.
    """

    class MockConfigEntry:
        def __init__(self):
            self.data = {
                "username": "test_user",
            }

    return MockConfigEntry()
