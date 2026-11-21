"""Endpoint URLs of the cloud API, built from one base URL."""

from urllib.parse import urlparse

from .exceptions import ValidationError
from .systems import ELMO_E_CONNECT


class Router:
    """API router class that holds a list of endpoints grouped by action type."""

    def __init__(self, base_url: str | None) -> None:
        """Build the endpoints from `base_url`.

        The client may replace the base URL after a login redirect. Every endpoint is built
        from the base URL held when it is read.

        Args:
            base_url: HTTPS root URL of the cloud API. Elmo e-Connect when None or empty.

        Raises:
            ValidationError: if the URL scheme is not `https`.
        """
        # Enforce the value is a valid URL behind HTTPS
        # Elmo e-Connect service must kept as default
        base_url = base_url or ELMO_E_CONNECT
        url = urlparse(base_url)
        if url.scheme != "https":
            raise ValidationError("The schema must be HTTPS")

        self._base_url = base_url

    @property
    def auth(self) -> str:
        """Login endpoint. A GET with the credentials returns the session ID and the panel details."""
        return f"{self._base_url}/api/login"

    @property
    def descriptions(self) -> str:
        """Endpoint that returns the names of sectors, inputs and outputs, keyed by class and index."""
        return f"{self._base_url}/api/strings"

    @property
    def update(self) -> str:
        """Long-polling endpoint that answers when sectors, inputs, outputs or alerts change."""
        return f"{self._base_url}/api/updates"

    @property
    def status(self) -> str:
        """Endpoint that returns the panel LEDs and anomalies, which the client reads as alerts."""
        return f"{self._base_url}/api/statusadv"

    @property
    def lock(self) -> str:
        """Endpoint that acquires the panel lock with the alarm code."""
        return f"{self._base_url}/api/panel/syncLogin"

    @property
    def unlock(self) -> str:
        """Endpoint that releases the panel lock."""
        return f"{self._base_url}/api/panel/syncLogout"

    @property
    def send_command(self) -> str:
        """Endpoint that arms, disarms, excludes, includes, or turns on or off panel elements."""
        return f"{self._base_url}/api/panel/syncSendCommand"

    @property
    def sectors(self) -> str:
        """Endpoint that lists the panel's sectors and their state."""
        return f"{self._base_url}/api/areas"

    @property
    def inputs(self) -> str:
        """Endpoint that lists the panel's inputs and their state."""
        return f"{self._base_url}/api/inputs"

    @property
    def outputs(self) -> str:
        """Endpoint that lists the panel's outputs and their state."""
        return f"{self._base_url}/api/outputs"
