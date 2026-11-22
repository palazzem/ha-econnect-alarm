import logging
from collections.abc import Iterator

import pytest
from homeassistant.config_entries import ConfigEntryState

from tests.scenarios.runner import BASE_URL, Endpoint, Moment, Row
from tests.scenarios.runner.cloud import Request
from tests.scenarios.runner.timeline import LogCapture, render


@pytest.fixture
def capture() -> Iterator[LogCapture]:
    capture = LogCapture()
    capture.attach()
    yield capture
    capture.detach()


def test_render_shows_each_row_with_its_requests_logs_and_changed_entities() -> None:
    rows = [
        Row(
            "setup",
            0,
            Moment.SETUP,
            ConfigEntryState.LOADED,
            (Request(Endpoint.LOGIN, Endpoint.LOGIN.url, "200"),),
            (),
            {"sensor.a": "on", "sensor.b": "off"},
        ),
        Row(
            "restart",
            0,
            Moment.RELOAD,
            ConfigEntryState.SETUP_RETRY,
            (
                Request(Endpoint.LOGIN, Endpoint.LOGIN.url, "ConnectionError"),
                Request(None, f"{BASE_URL}/api/unknown", "unknown"),
            ),
            ("ERROR custom_components.econnect_metronet: setup failed",),
            {"sensor.a": "unavailable", "sensor.b": "off"},
        ),
        Row(
            "restart",
            1,
            Moment.CYCLE,
            ConfigEntryState.SETUP_RETRY,
            (),
            (),
            {"sensor.a": "unavailable", "sensor.b": "off"},
        ),
    ]

    assert render(rows) == "\n".join(
        [
            "setup #0: entry=loaded unavailable=0/2",
            "    requests: login:200",
            "    sensor.a: - -> on",
            "    sensor.b: - -> off",
            "restart (reload): entry=setup_retry unavailable=1/2",
            f"    requests: login:ConnectionError {BASE_URL}/api/unknown:unknown",
            "    ERROR custom_components.econnect_metronet: setup failed",
            "    sensor.a: on -> unavailable",
            "restart #1: entry=setup_retry unavailable=1/2",
            "    requests: -",
        ]
    )


def test_log_capture_takes_the_warnings_and_errors_logged_since_the_last_take(capture: LogCapture) -> None:
    logger = logging.getLogger("custom_components.econnect_metronet.coordinator")
    logger.info("not shown")
    logger.warning("slow answer\nsecond line")
    try:
        raise ValueError("boom")
    except ValueError:
        logging.getLogger("homeassistant.helpers.update_coordinator").exception("refresh failed")
    logging.getLogger("homeassistant.core").error("not an observed logger")

    assert capture.take() == (
        "WARNING custom_components.econnect_metronet.coordinator: slow answer",
        "ERROR homeassistant.helpers.update_coordinator: refresh failed [ValueError]",
    )
    assert capture.take() == ()
