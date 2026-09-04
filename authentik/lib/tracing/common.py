"""Shared tracer protocol and no-op fallback"""

from contextlib import contextmanager
from typing import Any, Protocol

# Set by lifecycle/gunicorn.conf.py before the app is preloaded, to tell
# AuthentikCoreConfig.ready() to defer setup_post_fork() to gunicorn's post_fork hook
TRACER_DEFER_POSTFORK_ENV_VAR = "AUTHENTIK_TRACER_DEFER_POSTFORK"


class Span(Protocol):
    """Structural interface every tracer's span-like object satisfies"""

    description: str | None

    def set_data(self, key: str, value: Any) -> None: ...


class NoOpSpan:
    """Span yielded by the no-op tracer"""

    description: str | None = None

    def set_data(self, key: str, value: Any) -> None:
        pass


class Tracer:
    """Base tracer: the protocol every tracer follows, and the no-op fallback used
    when no error-reporting backend is configured"""

    def setup_pre_fork(self) -> None:
        pass

    def setup_post_fork(self) -> None:
        pass

    def record_exception(self, exc: Exception) -> None:
        pass

    def get_http_meta(self) -> dict[str, str]:
        return {}

    def set_tag(self, key: str, value: Any) -> None:
        pass

    @contextmanager
    def active_tracer().start_span(self, op: str, name: str | None = None):
        yield NoOpSpan()
