"""Guards for client methods that need an authenticated session or the panel lock."""

from collections.abc import Callable
from threading import Lock
from typing import Concatenate, ParamSpec, Protocol, TypeVar

from requests.exceptions import HTTPError

from .exceptions import InvalidToken, LockNotAcquired, MissingToken

_P = ParamSpec("_P")
_R = TypeVar("_R")


class _SessionHolder(Protocol):
    _session_id: str | None


class _LockHolder(Protocol):
    _lock: Lock


_S = TypeVar("_S", bound=_SessionHolder)
_L = TypeVar("_L", bound=_LockHolder)


def require_session(func: Callable[Concatenate[_S, _P], _R]) -> Callable[Concatenate[_S, _P], _R]:
    """Decorator applied to functions that require a valid Session.

    The session ID is verified in the instance for the attribute
    `_session_id`.

    Raises:
        MissingToken: if a `session_id` is not available.
        InvalidToken: if stored `session_id` is not valid (returns 401).
    """

    def func_wrapper(self: _S, /, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        if self._session_id is None:
            raise MissingToken
        else:
            try:
                return func(self, *args, **kwargs)
            except HTTPError as e:
                # Translate 401 into InvalidToken exception
                # Bubble up any other exception
                if e.response is not None and e.response.status_code == 401:
                    raise InvalidToken from e
                raise

    return func_wrapper


def require_lock(func: Callable[Concatenate[_L, _P], _R]) -> Callable[Concatenate[_L, _P], _R]:
    """Decorator applied to functions that require to obtain a system lock.

    The lock is verified in the instance for the attribute `_lock` that must
    be a `threading.Lock` class.

    Raises:
        LockNotAcquired: if a Lock is not acquired.
    """

    def func_wrapper(self: _L, /, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        # If the Lock() acquisition succeed it means a locking is not occurring
        # and so bail-out the execution (and release the lock).
        # TODO: Lock() state must be moved outside of this client, so that
        # it represents a stateless client.
        if not self._lock.locked():
            raise LockNotAcquired("A lock must be acquired via `lock()` method.")
        else:
            try:
                return func(self, *args, **kwargs)
            except HTTPError as err:
                # 403: Method has been called without obtaining the server lock
                if err.response is not None and err.response.status_code == 403:
                    self._lock.release()
                    raise LockNotAcquired("A lock must be acquired via `lock()` method.") from err
                raise

    return func_wrapper
