"""The scripted cloud: answers every HTTP request the integration sends with the reply a step scripts.

The cloud sits behind `responses`, so no request leaves the process and no socket is opened.
"""

import contextlib
import re
import threading
from dataclasses import dataclass
from typing import Final
from urllib.parse import urlsplit

import requests
import responses
from requests import PreparedRequest

from .endpoints import ALL_ENDPOINTS, Endpoint
from .replies import NORMAL, Replies, Reply

_ANY_URL: Final = re.compile(r".*")


def _reply_in_force(replies: Replies, endpoint: Endpoint) -> Reply:
    return replies.get(endpoint, replies.get(ALL_ENDPOINTS, NORMAL))


@dataclass(frozen=True)
class Request:
    """One request the cloud received, with what happened to it.

    Attributes:
        endpoint: The endpoint the request reached, or None for a URL outside the endpoint table.
        url: The request URL without its query string.
        result: The status code, the name of the exception raised, or `unknown`.
    """

    endpoint: Endpoint | None
    url: str
    result: str

    @property
    def unknown(self) -> bool:
        """Whether the request went to a URL outside the endpoint table."""
        return self.endpoint is None

    def __str__(self) -> str:
        """Render as `<endpoint>:<result>`, or `<url>:unknown` for an unknown URL."""
        return f"{self.endpoint.value if self.endpoint else self.url}:{self.result}"


class ScriptedCloud:
    """The e-Connect cloud as a scenario scripts it, behind every request `responses` intercepts.

    Each request gets the reply in force: the step's reply for its endpoint, else the one under `ALL_ENDPOINTS`,
    else a normal reply. A request to a URL outside the endpoint table raises `requests.ConnectionError` and is
    recorded as unknown. Requests arrive on Home Assistant's executor threads, so every method is thread safe.
    """

    def __init__(self) -> None:
        """Create a cloud that answers every endpoint normally."""
        self._replies: Replies = {}
        self._requests: list[Request] = []
        self._lock = threading.Lock()
        self._routes = {(endpoint.method, endpoint.url): endpoint for endpoint in Endpoint}

    def register(self, mock: responses.RequestsMock) -> None:
        """Route every `GET` and `POST` that `mock` intercepts, whatever its URL, to this cloud.

        One catch-all callback per method the client uses: `responses` would otherwise pick among several matching
        registrations itself.
        """
        for method in sorted({endpoint.method for endpoint in Endpoint}):
            mock.add_callback(method, _ANY_URL, callback=self._receive)

    def script(self, replies: Replies) -> None:
        """Answer the requests that arrive from now on with `replies`.

        Each endpoint's reply in force answers its fixture body once here, in the caller's thread, so a reply that
        cannot answer its endpoint fails the test that scripts it instead of an executor job the integration
        swallows.

        Raises:
            Exception: whatever a reply raises other than `requests.RequestException`, such as a `TypeError` for a
                predicate on an object body or a `KeyError` from a predicate reading a missing field.
        """
        for endpoint in Endpoint:
            with contextlib.suppress(requests.RequestException):
                _reply_in_force(replies, endpoint).answer(endpoint.body)
        with self._lock:
            self._replies = replies

    def take_requests(self) -> list[Request]:
        """Return the requests recorded since the last call, in the order they were answered."""
        with self._lock:
            taken, self._requests = self._requests, []
        return taken

    def _record(self, endpoint: Endpoint | None, url: str, result: str) -> None:
        with self._lock:
            self._requests.append(Request(endpoint, url, result))

    def _receive(self, request: PreparedRequest) -> tuple[int, dict[str, str], str]:
        parts = urlsplit(request.url or "")
        url = f"{parts.scheme}://{parts.netloc}{parts.path}"
        endpoint = self._routes.get((request.method or "", url))
        if endpoint is None:
            self._record(None, url, "unknown")
            raise requests.ConnectionError(f"Scripted cloud: no endpoint for {request.method} {url}")
        with self._lock:
            reply = _reply_in_force(self._replies, endpoint)
        try:
            status, body = reply.answer(endpoint.body)
        except requests.RequestException as exc:
            self._record(endpoint, url, type(exc).__name__)
            raise
        self._record(endpoint, url, str(status))
        return status, {}, body
