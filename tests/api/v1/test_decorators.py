from threading import Lock

import pytest
from requests.exceptions import HTTPError
from requests.models import Response

from custom_components.econnect_metronet.api.v1.decorators import require_lock, require_session
from custom_components.econnect_metronet.api.v1.exceptions import InvalidToken, LockNotAcquired, MissingToken


def test_require_session_present():
    """Should succeed if a session ID is available."""

    class TestClient:
        def __init__(self):
            # Session is available
            self._session_id = "test"
            self._session_expire = 9999999999

        @require_session
        def action(self):
            return 42

    client = TestClient()
    assert client.action() == 42


def test_require_session_missing():
    """Should fail if a session ID is not available."""

    class TestClient:
        def __init__(self):
            # Session is not available
            self._session_id = None

        @require_session
        def action(self):
            return 42

    client = TestClient()
    with pytest.raises(MissingToken) as excinfo:
        client.action()
    assert "No token is present" in str(excinfo.value)


def test_require_session_invalid():
    """Should fail if a session ID is not valid (API returns 401)."""

    class TestClient:
        def __init__(self):
            # Session is available
            self._session_id = "test"

        @require_session
        def action(self):
            # Raise a 401 to emulate lack of valid authentication credentials
            r = Response()
            r.status_code = 401
            raise HTTPError(response=r)

    client = TestClient()
    with pytest.raises(InvalidToken) as excinfo:
        client.action()
    assert "Used token is not valid" in str(excinfo.value)


def test_require_lock():
    """Should succeed if the lock has been acquired."""

    class TestClient:
        def __init__(self):
            # Lock attribute
            self._lock = Lock()

        @require_lock
        def action(self):
            return 42

    client = TestClient()
    client._lock.acquire()
    assert client.action() == 42


def test_require_lock_fails():
    """Should fail if the lock has not been acquired."""

    class TestClient:
        def __init__(self):
            # Lock attribute
            self._lock = Lock()

        @require_lock
        def action(self):
            return 42

    client = TestClient()
    with pytest.raises(LockNotAcquired):
        client.action()


def test_require_lock_not_valid():
    """Should fail if the obtained lock is not valid anymore (API returns 401)."""

    class TestClient:
        def __init__(self):
            # Lock attribute
            self._lock = Lock()

        @require_lock
        def action(self):
            # Raise a 403 to emulate lack of a valid Lock()
            r = Response()
            r.status_code = 403
            raise HTTPError(response=r)

    client = TestClient()
    with pytest.raises(LockNotAcquired):
        client.action()
