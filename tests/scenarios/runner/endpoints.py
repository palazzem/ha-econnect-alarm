"""The e-Connect cloud endpoints a scenario scripts, one per route of the client's router.

Each endpoint knows the HTTP method the client uses, the URL the client's `Router` builds from `BASE_URL`, and
the canned body a healthy cloud answers with. A route change in the client moves the endpoint with it.
"""

from enum import Enum
from typing import Final

from custom_components.econnect_metronet.api.v1.router import Router
from tests.fixtures import responses as canned

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
        """HTTP method the client sends: `GET` for login, `POST` for every other route."""
        return "GET" if self is Endpoint.LOGIN else "POST"

    @property
    def url(self) -> str:
        """Absolute URL of the route under `BASE_URL`, without a query string."""
        return _ROUTES[self][0]

    @property
    def body(self) -> str:
        """Canned body a healthy cloud answers this route with."""
        return _ROUTES[self][1]


class AllEndpoints(Enum):
    """Key of a step's replies that stands for every endpoint the step does not name."""

    ALL_ENDPOINTS = "*"


ALL_ENDPOINTS: Final = AllEndpoints.ALL_ENDPOINTS
"""The reply under this key answers every endpoint a step does not name explicitly."""

_ROUTES: Final = {
    Endpoint.LOGIN: (_ROUTER.auth, canned.LOGIN),
    Endpoint.STRINGS: (_ROUTER.descriptions, canned.STRINGS),
    Endpoint.UPDATES: (_ROUTER.update, canned.UPDATES),
    Endpoint.STATUSADV: (_ROUTER.status, canned.STATUS),
    Endpoint.AREAS: (_ROUTER.sectors, canned.AREAS),
    Endpoint.INPUTS: (_ROUTER.inputs, canned.INPUTS),
    Endpoint.OUTPUTS: (_ROUTER.outputs, canned.OUTPUTS),
    Endpoint.SYNC_LOGIN: (_ROUTER.lock, canned.SYNC_LOGIN),
    Endpoint.SYNC_LOGOUT: (_ROUTER.unlock, canned.SYNC_LOGOUT),
    Endpoint.SYNC_SEND_COMMAND: (_ROUTER.send_command, canned.SYNC_SEND_COMMAND),
}
