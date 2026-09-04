"""authentik error reporting: one active tracer handles spans/tags, but every
configured backend gets exceptions"""

from authentik.lib.config import CONFIG
from authentik.lib.tracing.common import (
    TRACER_DEFER_POSTFORK_ENV_VAR as TRACER_DEFER_POSTFORK_ENV_VAR,
)
from authentik.lib.tracing.common import Span as Span
from authentik.lib.tracing.common import Tracer
from authentik.lib.tracing.exceptions import TracingIgnoredException as TracingIgnoredException
from authentik.lib.tracing.exceptions import should_ignore_exception as should_ignore_exception
from authentik.lib.tracing.sentry import SentryTracer

_enabled = CONFIG.get_bool("error_reporting.enabled", False)
_sentry_tracer = SentryTracer() if _enabled and CONFIG.get("error_reporting.sentry_dsn") else None
# Every configured backend gets exceptions; only one of them handles spans/tags, since
# authentik only ever needs one trace tree and picking one avoids double request overhead
_error_tracers: list[Tracer] = [t for t in (_sentry_tracer) if t is not None]
_active_tracer: Tracer = _sentry_tracer or Tracer()


def active_tracer() -> Tracer:
    """Get the tracer used for spans, tags, and trace-context propagation headers"""
    return _active_tracer


def setup_pre_fork() -> None:
    """Initialize every configured backend before any fork"""
    for backend in _error_tracers:
        backend.setup_pre_fork()


def setup_post_fork() -> None:
    """Finish initializing every configured backend after a fork"""
    for backend in _error_tracers:
        backend.setup_post_fork()


def init() -> None:
    """Full init for single-process entrypoints that never fork afterwards. Gunicorn's
    preloaded web server calls setup_pre_fork()/setup_post_fork() separately instead"""
    setup_pre_fork()
    setup_post_fork()


def record_exception(exc: Exception) -> None:
    """Record an exception on every configured backend"""
    for backend in _error_tracers:
        backend.record_exception(exc)
