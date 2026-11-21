from collections.abc import Iterator

import pytest
import requests
import responses

from tests.scenarios.runner import (
    ALL_ENDPOINTS,
    BASE_URL,
    CONNECTION_ERROR,
    NORMAL,
    PANEL_DISCONNECTED,
    SERVER_ERROR,
    Edited,
    Endpoint,
    Reply,
)
from tests.scenarios.runner.cloud import ScriptedCloud


@pytest.fixture
def cloud() -> Iterator[ScriptedCloud]:
    cloud = ScriptedCloud()
    with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
        cloud.register(mock)
        yield cloud


def call(endpoint: Endpoint) -> requests.Response:
    return requests.request(endpoint.method, endpoint.url, timeout=5)


def test_a_scripted_request_is_answered_with_sockets_blocked(cloud: ScriptedCloud) -> None:
    response = call(Endpoint.LOGIN)

    assert response.status_code == 200
    assert response.text == Endpoint.LOGIN.body


def test_an_endpoint_no_step_names_answers_normally(cloud: ScriptedCloud) -> None:
    cloud.script({Endpoint.AREAS: SERVER_ERROR})

    response = call(Endpoint.INPUTS)

    assert response.status_code == 200
    assert response.text == Endpoint.INPUTS.body


def test_the_reply_for_all_endpoints_answers_every_endpoint_the_step_does_not_name(cloud: ScriptedCloud) -> None:
    cloud.script({ALL_ENDPOINTS: PANEL_DISCONNECTED, Endpoint.LOGIN: NORMAL})

    assert call(Endpoint.LOGIN).status_code == 200
    assert call(Endpoint.AREAS).status_code == 403
    assert [str(request) for request in cloud.take_requests()] == ["login:200", "areas:403"]


def test_a_transport_error_raises_and_is_recorded_by_exception_name(cloud: ScriptedCloud) -> None:
    cloud.script({Endpoint.UPDATES: CONNECTION_ERROR})

    with pytest.raises(requests.ConnectionError):
        call(Endpoint.UPDATES)

    assert [str(request) for request in cloud.take_requests()] == ["updates:ConnectionError"]


def test_a_request_to_an_unknown_url_fails_and_is_recorded_as_unknown(cloud: ScriptedCloud) -> None:
    with pytest.raises(requests.ConnectionError):
        requests.post(f"{BASE_URL}/api/unknown", timeout=5)

    [request] = cloud.take_requests()
    assert request.unknown
    assert str(request) == f"{BASE_URL}/api/unknown:unknown"


@pytest.mark.parametrize(
    ("endpoint", "reply", "error"),
    [
        (Endpoint.UPDATES, Edited({"Areas": False}, where=lambda entry: True), TypeError),
        (Endpoint.INPUTS, Edited({"InUse": False}, where=lambda entry: entry["Missing"] == 1), KeyError),
    ],
    ids=["predicate on an object body", "predicate reading a missing field"],
)
def test_scripting_a_reply_that_cannot_answer_its_endpoint_raises(
    cloud: ScriptedCloud, endpoint: Endpoint, reply: Reply, error: type[Exception]
) -> None:
    with pytest.raises(error):
        cloud.script({endpoint: reply})


def test_scripting_a_transport_error_for_every_endpoint_is_accepted(cloud: ScriptedCloud) -> None:
    cloud.script({ALL_ENDPOINTS: CONNECTION_ERROR})

    with pytest.raises(requests.ConnectionError):
        call(Endpoint.LOGIN)


def test_a_known_url_called_with_another_method_is_recorded_as_unknown(cloud: ScriptedCloud) -> None:
    with pytest.raises(requests.ConnectionError):
        requests.get(Endpoint.AREAS.url, timeout=5)

    [request] = cloud.take_requests()
    assert request.unknown
    assert str(request) == f"{Endpoint.AREAS.url}:unknown"
