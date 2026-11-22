"""The e-Connect cloud endpoints a scenario scripts, one per route of the client's router.

Each endpoint knows the HTTP method the client uses, the URL the client's `Router` builds from `BASE_URL`, and
the fixture body a healthy cloud answers with. A route change in the client moves the endpoint with it.
"""

from enum import Enum
from typing import Final, NamedTuple

from custom_components.econnect_metronet.api.v1.router import Router
from tests.fixtures import responses as fixtures

BASE_URL: Final = "https://example.com"
"""Root URL of the scripted cloud; the scenario's config entry points the integration at it."""

_ROUTER: Final = Router(BASE_URL)


class Endpoint(Enum):
    """A route of the e-Connect cloud API, keyed in a step's replies.

    The value is the route's name as the cloud spells it, shown in the timeline.
    """

    LOGIN = "login"
    STRINGS = "strings"
    UPDATES = "updates"
    STATUSADV = "statusadv"
    AREAS = "areas"
    INPUTS = "inputs"
    OUTPUTS = "outputs"
    SYNC_LOGIN = "syncLogin"
    SYNC_LOGOUT = "syncLogout"
    SYNC_SEND_COMMAND = "syncSendCommand"

    @property
    def method(self) -> str:
        """HTTP method the client sends to the route."""
        return _ROUTES[self].method

    @property
    def url(self) -> str:
        """Absolute URL of the route under `BASE_URL`, without a query string."""
        return _ROUTES[self].url

    @property
    def body(self) -> str:
        """Fixture body a healthy cloud answers this route with."""
        return _ROUTES[self].body


class AllEndpoints(Enum):
    """Key of a step's replies that stands for every endpoint the step does not name."""

    ALL_ENDPOINTS = "*"


ALL_ENDPOINTS: Final = AllEndpoints.ALL_ENDPOINTS
"""The reply under this key answers every endpoint a step does not name explicitly."""


class _Route(NamedTuple):
    method: str
    url: str
    body: str


_ROUTES: Final = {
    Endpoint.LOGIN: _Route("GET", _ROUTER.auth, fixtures.LOGIN),
    Endpoint.STRINGS: _Route("POST", _ROUTER.descriptions, fixtures.STRINGS),
    Endpoint.UPDATES: _Route("POST", _ROUTER.update, fixtures.UPDATES),
    Endpoint.STATUSADV: _Route("POST", _ROUTER.status, fixtures.STATUS),
    Endpoint.AREAS: _Route("POST", _ROUTER.sectors, fixtures.AREAS),
    Endpoint.INPUTS: _Route("POST", _ROUTER.inputs, fixtures.INPUTS),
    Endpoint.OUTPUTS: _Route("POST", _ROUTER.outputs, fixtures.OUTPUTS),
    Endpoint.SYNC_LOGIN: _Route("POST", _ROUTER.lock, fixtures.SYNC_LOGIN),
    Endpoint.SYNC_LOGOUT: _Route("POST", _ROUTER.unlock, fixtures.SYNC_LOGOUT),
    Endpoint.SYNC_SEND_COMMAND: _Route("POST", _ROUTER.send_command, fixtures.SYNC_SEND_COMMAND),
}
