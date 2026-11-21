"""Steps, expectations, and the runner that plays them against the integration inside Home Assistant.

The runner sets the integration up through a config entry against a healthy scripted cloud, records the state of
every entity of the entry as the baseline, then plays each step: an optional reload of the entry, then one
coordinator cycle at a time on a fake clock. Only the clock and the cloud are faked; Home Assistant's event loop,
executor, coordinator scheduling, entity registry, and state machine are real.
"""

import fnmatch
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Final

import responses
from freezegun.api import FrozenDateTimeFactory
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant.common import MockConfigEntry, async_fire_time_changed

from custom_components.econnect_metronet.config_flow import EconnectConfigFlow
from custom_components.econnect_metronet.const import (
    CONF_DOMAIN,
    CONF_SCAN_INTERVAL,
    CONF_SYSTEM_URL,
    DOMAIN,
    SCAN_INTERVAL_DEFAULT,
)

from .cloud import ScriptedCloud
from .endpoints import BASE_URL
from .replies import Replies
from .timeline import LogCapture, Moment, Row, render

ABSENT: Final = "<absent>"
"""State shown for an entity the registry holds but the state machine does not."""


class ScenarioFailed(AssertionError):
    """A scenario broke an expectation, or made a request no endpoint answers.

    The message states what went wrong, then the whole timeline.
    """


@dataclass(frozen=True)
class Expect:
    """What must hold when a step ends, checked against the step's last timeline row.

    Each pattern is an entity id glob, as `fnmatch` reads it, matched against the entities of the config entry; a
    pattern that matches no entity is a failure.

    Attributes:
        available: Entities that must not be `unavailable`.
        unavailable: Entities that must be `unavailable`.
        at_baseline: Entities that must hold the state they had right after setup.
        entry_state: State the config entry must be in, or None to leave it unchecked.

    Example:
        `Expect(unavailable=["sensor.*"], entry_state=ConfigEntryState.LOADED)`
    """

    available: Sequence[str] = ()
    unavailable: Sequence[str] = ()
    at_baseline: Sequence[str] = ()
    entry_state: ConfigEntryState | None = None

    def check(self, row: Row, baseline: Mapping[str, str]) -> list[str]:
        """Return one line per way `row` breaks this expectation, naming each entity; empty if it holds.

        Args:
            row: The row to check; only its entity states and config entry state are read.
            baseline: The state of each entity right after setup, by entity id.
        """
        states = row.states
        failures = [
            f"{pattern} matches no entity"
            for pattern in (*self.available, *self.unavailable, *self.at_baseline)
            if not fnmatch.filter(states, pattern)
        ]
        failures += [
            f"{entity_id} is unavailable, expected available"
            for entity_id in _matching(states, self.available)
            if states[entity_id] == STATE_UNAVAILABLE
        ]
        failures += [
            f"{entity_id} is {states[entity_id]}, expected unavailable"
            for entity_id in _matching(states, self.unavailable)
            if states[entity_id] != STATE_UNAVAILABLE
        ]
        failures += [
            f"{entity_id} is {states[entity_id]}, expected its baseline {baseline.get(entity_id, ABSENT)}"
            for entity_id in _matching(states, self.at_baseline)
            if states[entity_id] != baseline.get(entity_id, ABSENT)
        ]
        if self.entry_state is not None and row.entry_state is not self.entry_state:
            failures.append(f"config entry is {row.entry_state.value}, expected {self.entry_state.value}")
        return failures


def _matching(states: Mapping[str, str], patterns: Sequence[str]) -> list[str]:
    return sorted({entity_id for pattern in patterns for entity_id in fnmatch.filter(states, pattern)})


@dataclass(frozen=True)
class Step:
    """A number of coordinator cycles during which the cloud answers with the same replies.

    Attributes:
        name: Name shown in the timeline and in failures.
        cycles: Coordinator cycles to play.
        cycle_seconds: Seconds the clock moves per cycle; None for the config entry's scan interval.
        replies: What the cloud answers during the step; an endpoint the step does not name answers normally.
        reload: Whether to reload the config entry, as a Home Assistant restart does, before the first cycle.
        expect: What must hold on the step's last row; None checks nothing.

    Example:
        `Step("panel offline", cycles=5, replies={ALL_ENDPOINTS: PANEL_DISCONNECTED, Endpoint.LOGIN: NORMAL})`
    """

    name: str
    cycles: int = 1
    cycle_seconds: float | None = None
    replies: Replies = field(default_factory=dict)
    reload: bool = False
    expect: Expect | None = None


class Scenario:
    """Plays steps against the integration, set up through a config entry in `hass`.

    Observes the integration only through Home Assistant: the entity registry, the state machine, the config
    entry state, and log records.
    """

    def __init__(self, hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
        """Bind the runner to `hass` and to the fake clock `freezer` that moves Home Assistant's time."""
        self._hass = hass
        self._freezer = freezer
        self._cloud = ScriptedCloud()
        self._logs = LogCapture()
        self._rows: list[Row] = []
        self._baseline: Mapping[str, str] = {}
        self._entry = MockConfigEntry(
            version=EconnectConfigFlow.VERSION,
            domain=DOMAIN,
            data={
                CONF_USERNAME: "scenario",
                CONF_PASSWORD: "scenario-password",
                CONF_DOMAIN: "domain",
                CONF_SYSTEM_URL: BASE_URL,
            },
        )

    @property
    def timeline(self) -> Sequence[Row]:
        """The rows recorded so far, in order."""
        return self._rows

    async def run(self, *steps: Step) -> None:
        """Set up the config entry against a healthy cloud, then play `steps` in order.

        After each reload and each cycle the runner waits, with `async_block_till_done`, until Home Assistant has no
        pending work, then records a row. The config entry is unloaded before this returns or raises.

        Raises:
            ScenarioFailed: if setup does not load the entry, a step's expectation fails on the step's last row, or a
                request reaches a URL no endpoint answers.
        """
        with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
            self._cloud.register(mock)
            self._logs.attach()
            try:
                await self._setup()
                for step in steps:
                    await self._play(step)
            finally:
                self._logs.detach()
                if self._entry.state in (ConfigEntryState.LOADED, ConfigEntryState.SETUP_RETRY):
                    await self._hass.config_entries.async_unload(self._entry.entry_id)
                await self._settle()

    async def _setup(self) -> None:
        self._entry.add_to_hass(self._hass)
        await self._hass.config_entries.async_setup(self._entry.entry_id)
        await self._settle()
        row = self._record("setup", 0, Moment.SETUP)
        self._baseline = row.states
        if row.entry_state is not ConfigEntryState.LOADED:
            self._fail(f"setup left the config entry {row.entry_state.value}, expected loaded")

    async def _play(self, step: Step) -> None:
        self._cloud.script(step.replies)
        last = self._rows[-1]
        if step.reload:
            await self._hass.config_entries.async_reload(self._entry.entry_id)
            await self._settle()
            last = self._record(step.name, 0, Moment.RELOAD)
        cycle = timedelta(seconds=step.cycle_seconds or self._scan_interval())
        for number in range(1, step.cycles + 1):
            self._freezer.tick(cycle)
            async_fire_time_changed(self._hass, dt_util.utcnow())
            await self._settle()
            last = self._record(step.name, number, Moment.CYCLE)
        if step.expect is not None:
            failures = step.expect.check(last, self._baseline)
            if failures:
                self._fail(f"step '{step.name}' broke its expectation at {last.label}:\n  " + "\n  ".join(failures))

    async def _settle(self) -> None:
        await self._hass.async_block_till_done(wait_background_tasks=True)

    def _scan_interval(self) -> int:
        interval: int = self._entry.options.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL_DEFAULT)
        return interval

    def _states(self) -> dict[str, str]:
        entries = er.async_entries_for_config_entry(er.async_get(self._hass), self._entry.entry_id)
        states = {}
        for entity_id in sorted(entry.entity_id for entry in entries if entry.disabled_by is None):
            state = self._hass.states.get(entity_id)
            states[entity_id] = state.state if state is not None else ABSENT
        return states

    def _record(self, step: str, cycle: int, moment: Moment) -> Row:
        requests = tuple(self._cloud.take_requests())
        row = Row(step, cycle, moment, self._entry.state, requests, self._logs.take(), self._states())
        self._rows.append(row)
        unknown = [str(request) for request in requests if request.unknown]
        if unknown:
            self._fail(f"{row.label} made requests no endpoint answers: {' '.join(unknown)}")
        return row

    def _fail(self, reason: str) -> None:
        raise ScenarioFailed(f"{reason}\n\nTimeline:\n{render(self._rows)}")
