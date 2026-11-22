"""What the scripted cloud answers to a request, as immutable values.

Each reply turns an endpoint's fixture body into the HTTP status and body the client receives, or raises the
exception `requests` would raise. Named replies are named for what the cloud does, never for the test that uses them.
"""

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Final

import requests

from .endpoints import AllEndpoints, Endpoint

Entry = Mapping[str, Any]
"""One entry of a list body, such as a sector, an input, or an output."""


@dataclass(frozen=True)
class Normal:
    """A healthy cloud: 200 with the endpoint's fixture body."""

    def answer(self, body: str) -> tuple[int, str]:
        """Return status 200 and `body` unchanged."""
        return 200, body


@dataclass(frozen=True)
class Edited:
    """200 with the fixture body after a change.

    On a list body, every entry gets `changes`, or only the entries `where` selects. On an object body, the keys in
    `changes` are set and every other key is kept.

    Example:
        `Edited({"InUse": False}, where=lambda entry: entry["Index"] == 1)` answers inputs whose second entry is no
        longer in use.
    """

    changes: Mapping[str, Any]
    where: Callable[[Entry], bool] | None = None

    def answer(self, body: str) -> tuple[int, str]:
        """Return status 200 and `body` with `changes` applied.

        Raises:
            TypeError: if `where` is set and `body` is not a JSON list.
        """
        data = json.loads(body)
        if isinstance(data, list):
            selected = self.where or (lambda entry: True)
            data = [{**entry, **self.changes} if selected(entry) else entry for entry in data]
        elif self.where is not None:
            raise TypeError("Edited: a predicate selects list entries, but the body is a JSON object")
        else:
            data = {**data, **self.changes}
        return 200, json.dumps(data)


@dataclass(frozen=True)
class Status:
    """The cloud answers with an HTTP status and a body text, such as 401, 403, or 5xx."""

    code: int
    text: str = ""

    def answer(self, body: str) -> tuple[int, str]:
        """Return `code` and `text`; the fixture body is ignored."""
        return self.code, self.text


@dataclass(frozen=True)
class TransportError:
    """The request never gets an HTTP answer: `requests` raises `exception` with `message`."""

    exception: type[requests.RequestException]
    message: str

    def answer(self, body: str) -> tuple[int, str]:
        """Raise a new `exception` built from `message`.

        Raises:
            requests.RequestException: always, of type `exception`.
        """
        raise self.exception(self.message)


Reply = Normal | Edited | Status | TransportError
"""Anything a step can script for an endpoint."""

Replies = Mapping[Endpoint | AllEndpoints, Reply]
"""What a step scripts: a reply per endpoint, and optionally one under `ALL_ENDPOINTS` for every other endpoint."""

NORMAL: Final = Normal()
"""A healthy cloud."""

PANEL_DISCONNECTED: Final = Status(403, "Centrale non connessa")
"""The cloud is up but the panel is not connected to it."""

UNAUTHORIZED: Final = Status(401, "Unauthorized")
"""The session expired or the credentials are rejected."""

SERVER_ERROR: Final = Status(500, "Internal Server Error")
"""The cloud fails while handling the request."""

CONNECTION_ERROR: Final = TransportError(requests.ConnectionError, "connection refused")
"""The network is down: the connection to the cloud is refused."""

READ_TIMEOUT: Final = TransportError(requests.ReadTimeout, "read timed out")
"""The cloud accepts the connection but does not answer in time."""

NO_CHANGES: Final = Edited({"HasChanges": False, "Areas": False, "Inputs": False, "Outputs": False, "StatusAdv": False})
"""The long poll answers that nothing changed on the panel."""

IDS_RESET: Final = Edited({"Id": 1})
"""Sectors, inputs, or outputs come back with every id reset to 1."""
