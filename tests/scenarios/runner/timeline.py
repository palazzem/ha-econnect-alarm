"""The timeline of a scenario: one row after setup and one per cycle and reload, printed when a scenario fails.

A row holds only what Home Assistant shows: the config entry state, the requests the cloud received, the warnings
and errors logged, and the state of every entity of the config entry.
"""

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Final

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE

from .cloud import Request

LOGGERS: Final = ("custom_components.econnect_metronet", "homeassistant.helpers")
"""Loggers whose warnings and errors the timeline shows: the integration's and Home Assistant's helpers'."""


class Moment(Enum):
    """When in a scenario a row was recorded."""

    SETUP = "setup"
    """Right after the config entry was set up against a healthy cloud."""

    RELOAD = "reload"
    """Right after a step reloaded the config entry, before its first cycle."""

    CYCLE = "cycle"
    """After one coordinator cycle."""


@dataclass(frozen=True)
class Row:
    """What Home Assistant showed at one point of a scenario.

    Attributes:
        step: Name of the step, or `setup` for the row recorded right after setup.
        cycle: Coordinator cycle within the step, from 1; 0 for the setup and reload rows.
        moment: When in the scenario the row was recorded.
        entry_state: State of the config entry.
        requests: Requests the cloud received since the previous row, with their results, in order.
        logs: Warnings and errors logged since the previous row, one line each.
        states: State of every entity of the config entry, by entity id.
    """

    step: str
    cycle: int
    moment: Moment
    entry_state: ConfigEntryState
    requests: tuple[Request, ...]
    logs: tuple[str, ...]
    states: Mapping[str, str]

    @property
    def label(self) -> str:
        """Name of the row in the timeline and in failures: `<step> #<cycle>`, or `<step> (reload)`."""
        return f"{self.step} (reload)" if self.moment is Moment.RELOAD else f"{self.step} #{self.cycle}"

    @property
    def unavailable(self) -> int:
        """Number of entities whose state is `unavailable`."""
        return sum(state == STATE_UNAVAILABLE for state in self.states.values())


class LogCapture(logging.Handler):
    """Collects the WARNING and ERROR records of `LOGGERS` while attached."""

    def __init__(self) -> None:
        """Create a handler with no records, not attached to any logger."""
        super().__init__(logging.WARNING)
        self._lines: list[str] = []

    def attach(self) -> None:
        """Start collecting the records of every logger in `LOGGERS` and its children."""
        for name in LOGGERS:
            logging.getLogger(name).addHandler(self)

    def detach(self) -> None:
        """Stop collecting records."""
        for name in LOGGERS:
            logging.getLogger(name).removeHandler(self)

    def emit(self, record: logging.LogRecord) -> None:
        """Keep the first line of `record`'s message, with its level, logger, and exception type."""
        line = f"{record.levelname} {record.name}: {record.getMessage().splitlines()[0]}"
        if record.exc_info and record.exc_info[0] is not None:
            line += f" [{record.exc_info[0].__name__}]"
        self._lines.append(line)

    def take(self) -> tuple[str, ...]:
        """Return the lines collected since the last call, in the order logged."""
        self.acquire()
        try:
            lines, self._lines = self._lines, []
        finally:
            self.release()
        return tuple(lines)


def render(rows: Sequence[Row]) -> str:
    """Render `rows` as text: each row's header, then its requests, logs, and entities changed since the row before.

    The first row lists every entity with its state, which is the scenario's baseline.
    """
    lines: list[str] = []
    previous: Mapping[str, str] = {}
    for row in rows:
        lines.append(f"{row.label}: entry={row.entry_state.value} unavailable={row.unavailable}/{len(row.states)}")
        lines.append(f"    requests: {' '.join(str(request) for request in row.requests) or '-'}")
        lines.extend(f"    {line}" for line in row.logs)
        for entity_id, state in row.states.items():
            if previous.get(entity_id) != state:
                lines.append(f"    {entity_id}: {previous.get(entity_id, '-')} -> {state}")
        previous = row.states
    return "\n".join(lines)
