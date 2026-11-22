"""Scenario runner: reproduce what the e-Connect cloud does, cycle by cycle, against the integration in Home Assistant.

A scenario is data. Each step scripts what every endpoint answers for a number of coordinator cycles and states
what must hold when it ends; the runner advances Home Assistant's clock and records a timeline that it prints when a
scenario fails.
"""

from .endpoints import ALL_ENDPOINTS, BASE_URL, AllEndpoints, Endpoint
from .replies import (
    CONNECTION_ERROR,
    IDS_RESET,
    NO_CHANGES,
    NORMAL,
    PANEL_DISCONNECTED,
    READ_TIMEOUT,
    SERVER_ERROR,
    UNAUTHORIZED,
    Edited,
    Normal,
    Replies,
    Reply,
    Status,
    TransportError,
)
from .scenario import Expect, Scenario, ScenarioFailed, Step
from .timeline import Moment, Row

__all__ = [
    "ALL_ENDPOINTS",
    "BASE_URL",
    "CONNECTION_ERROR",
    "IDS_RESET",
    "NORMAL",
    "NO_CHANGES",
    "PANEL_DISCONNECTED",
    "READ_TIMEOUT",
    "SERVER_ERROR",
    "UNAUTHORIZED",
    "AllEndpoints",
    "Edited",
    "Endpoint",
    "Expect",
    "Moment",
    "Normal",
    "Replies",
    "Reply",
    "Row",
    "Scenario",
    "ScenarioFailed",
    "Status",
    "Step",
    "TransportError",
]
