from datetime import timedelta

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.util import dt as dt_util

from tests.scenarios.runner import (
    ALL_ENDPOINTS,
    CONNECTION_ERROR,
    NO_CHANGES,
    Edited,
    Endpoint,
    Expect,
    Moment,
    Row,
    Scenario,
    ScenarioFailed,
    Step,
)

PANEL = "alarm_control_panel.econnect_metronet_scenario"
REDIRECT_TO_UNKNOWN = Edited({"Redirect": True, "RedirectTo": "https://unknown.example"})


def results(scenario: Scenario, step: str) -> list[list[str]]:
    return [
        [str(request) for request in row.requests]
        for row in scenario.timeline
        if row.step == step and row.moment is Moment.CYCLE
    ]


def row(states: dict[str, str], entry_state: ConfigEntryState = ConfigEntryState.LOADED) -> Row:
    return Row("step", 1, Moment.CYCLE, entry_state, (), (), states)


async def test_one_cycle_advances_the_clock_once_by_the_scan_interval(scenario: Scenario) -> None:
    start = dt_util.utcnow()

    await scenario.run(Step("idle", cycles=3, replies={Endpoint.UPDATES: NO_CHANGES}))

    assert dt_util.utcnow() - start == timedelta(seconds=3 * 5)
    assert [requests.count("updates:200") for requests in results(scenario, "idle")] == [1, 1, 1]


async def test_a_cycle_lasts_the_seconds_its_step_states(scenario: Scenario) -> None:
    start = dt_util.utcnow()

    await scenario.run(Step("slow", cycles=2, cycle_seconds=8, replies={Endpoint.UPDATES: NO_CHANGES}))

    assert dt_util.utcnow() - start == timedelta(seconds=2 * 8)


async def test_a_reload_step_reloads_the_config_entry_and_records_a_row(scenario: Scenario) -> None:
    await scenario.run(Step("restart", cycles=1, reload=True))

    [reload_row] = [row for row in scenario.timeline if row.moment is Moment.RELOAD]
    assert reload_row.step == "restart"
    assert reload_row.entry_state is ConfigEntryState.LOADED
    assert "login:200" in [str(request) for request in reload_row.requests]


async def test_a_request_to_an_unknown_url_fails_the_scenario_in_the_row_that_shows_it(scenario: Scenario) -> None:
    with pytest.raises(ScenarioFailed, match="https://unknown.example/api/login:unknown"):
        await scenario.run(
            Step("redirected", cycles=1, reload=True, replies={Endpoint.LOGIN: REDIRECT_TO_UNKNOWN}),
            Step("never played", cycles=1),
        )

    last = scenario.timeline[-1]
    assert (last.step, last.moment) == ("redirected", Moment.RELOAD)
    assert any(request.unknown for request in last.requests)


async def test_a_reply_that_cannot_answer_its_endpoint_fails_the_scenario_before_its_step_plays(
    scenario: Scenario,
) -> None:
    broken = Edited({"InUse": False}, where=lambda entry: entry["Missing"] == 1)

    with pytest.raises(KeyError):
        await scenario.run(Step("broken script", cycles=1, replies={Endpoint.INPUTS: broken}))

    assert [row.step for row in scenario.timeline] == ["setup"]


async def test_a_failed_expectation_names_each_entity_and_prints_the_timeline(scenario: Scenario) -> None:
    with pytest.raises(ScenarioFailed) as failure:
        await scenario.run(
            Step(
                "outage",
                cycles=2,
                replies={ALL_ENDPOINTS: CONNECTION_ERROR},
                expect=Expect(available=["alarm_control_panel.*"]),
            )
        )

    message = str(failure.value)
    assert f"{PANEL} is unavailable, expected available" in message
    assert "setup #0: entry=loaded" in message
    assert "outage #2: entry=loaded" in message


async def test_an_expectation_is_checked_against_the_last_row_of_its_step(scenario: Scenario) -> None:
    await scenario.run(
        Step(
            "outage",
            cycles=1,
            replies={ALL_ENDPOINTS: CONNECTION_ERROR},
            expect=Expect(unavailable=["alarm_control_panel.*"]),
        )
    )

    assert scenario.timeline[0].states[PANEL] != "unavailable"
    assert scenario.timeline[-1].states[PANEL] == "unavailable"


async def test_a_failed_expectation_names_the_row_it_checked(scenario: Scenario) -> None:
    with pytest.raises(ScenarioFailed, match="step 'outage' broke its expectation at outage #3"):
        await scenario.run(
            Step(
                "outage",
                cycles=3,
                replies={ALL_ENDPOINTS: CONNECTION_ERROR},
                expect=Expect(at_baseline=["alarm_control_panel.*"]),
            )
        )

    last = scenario.timeline[-1]
    assert (last.step, last.cycle) == ("outage", 3)
    assert last.states[PANEL] == "unavailable"


async def test_the_timeline_is_not_printed_when_the_scenario_passes(
    scenario: Scenario, capsys: pytest.CaptureFixture[str]
) -> None:
    await scenario.run(Step("idle", cycles=1, expect=Expect(available=["*"])))

    assert capsys.readouterr().out == ""


def test_available_fails_for_an_unavailable_entity() -> None:
    failures = Expect(available=["sensor.*"]).check(row({"sensor.a": "unavailable", "sensor.b": "on"}), {})

    assert failures == ["sensor.a is unavailable, expected available"]


def test_unavailable_fails_for_an_available_entity() -> None:
    failures = Expect(unavailable=["sensor.*"]).check(row({"sensor.a": "unavailable", "sensor.b": "on"}), {})

    assert failures == ["sensor.b is on, expected unavailable"]


def test_at_baseline_fails_for_an_entity_whose_state_changed_since_setup() -> None:
    baseline = {"sensor.a": "on", "sensor.b": "off"}

    failures = Expect(at_baseline=["sensor.*"]).check(row({"sensor.a": "on", "sensor.b": "on"}), baseline)

    assert failures == ["sensor.b is on, expected its baseline off"]


def test_entry_state_fails_for_another_config_entry_state() -> None:
    expect = Expect(entry_state=ConfigEntryState.LOADED)

    failures = expect.check(row({}, entry_state=ConfigEntryState.SETUP_RETRY), {})

    assert failures == ["config entry is setup_retry, expected loaded"]


def test_a_pattern_that_matches_no_entity_fails() -> None:
    failures = Expect(available=["switch.*"]).check(row({"sensor.a": "on"}), {})

    assert failures == ["switch.* matches no entity"]


def test_an_expectation_that_holds_has_no_failures() -> None:
    expect = Expect(
        available=["sensor.a"],
        unavailable=["sensor.b"],
        at_baseline=["sensor.*"],
        entry_state=ConfigEntryState.LOADED,
    )

    states = {"sensor.a": "on", "sensor.b": "unavailable"}

    assert expect.check(row(states), baseline=states) == []
