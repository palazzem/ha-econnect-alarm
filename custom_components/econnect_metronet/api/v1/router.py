from urllib.parse import urlparse

from .exceptions import ValidationError
from .systems import ELMO_E_CONNECT


class Router:
    """API router class that holds a list of endpoints grouped by action type."""

    def __init__(self, base_url: str | None) -> None:
        # Enforce the value is a valid URL behind HTTPS
        # Elmo e-Connect service must kept as default
        base_url = base_url or ELMO_E_CONNECT
        url = urlparse(base_url)
        if url.scheme != "https":
            raise ValidationError("The schema must be HTTPS")

        self._base_url = base_url

    @property
    def auth(self) -> str:
        return f"{self._base_url}/api/login"

    @property
    def descriptions(self) -> str:
        return f"{self._base_url}/api/strings"

    @property
    def update(self) -> str:
        return f"{self._base_url}/api/updates"

    @property
    def status(self) -> str:
        return f"{self._base_url}/api/statusadv"

    @property
    def lock(self) -> str:
        return f"{self._base_url}/api/panel/syncLogin"

    @property
    def unlock(self) -> str:
        return f"{self._base_url}/api/panel/syncLogout"

    @property
    def send_command(self) -> str:
        return f"{self._base_url}/api/panel/syncSendCommand"

    @property
    def sectors(self) -> str:
        return f"{self._base_url}/api/areas"

    @property
    def inputs(self) -> str:
        return f"{self._base_url}/api/inputs"

    @property
    def outputs(self) -> str:
        return f"{self._base_url}/api/outputs"
