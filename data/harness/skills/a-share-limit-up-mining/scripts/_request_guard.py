from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Callable, TypeVar


T = TypeVar("T")


@contextmanager
def bounded_requests(timeout_seconds: int = 12):
    """Inject a finite timeout into requests calls that omit one."""
    import requests

    original = requests.sessions.Session.request

    def guarded(session, method, url, **kwargs):
        if kwargs.get("timeout") is None:
            kwargs["timeout"] = timeout_seconds
        return original(session, method, url, **kwargs)

    requests.sessions.Session.request = guarded
    try:
        yield
    finally:
        requests.sessions.Session.request = original


def call_with_retries(
    operation: Callable[[], T], *, attempts: int = 2, timeout_seconds: int = 12
) -> T:
    """Run a requests-backed operation with bounded retries."""
    if attempts < 1:
        raise ValueError("attempts must be positive")
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            with bounded_requests(timeout_seconds):
                return operation()
        except Exception as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(0.6 * (attempt + 1))
    assert last_error is not None
    raise last_error
