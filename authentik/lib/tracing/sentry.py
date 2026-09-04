"""authentik Sentry integration"""

from contextlib import contextmanager
from typing import Any

import sentry_sdk
from django.conf import settings
from sentry_sdk import HttpTransport, get_current_scope
from sentry_sdk.integrations.argv import ArgvIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.dramatiq import DramatiqIntegration
from sentry_sdk.integrations.socket import SocketIntegration
from sentry_sdk.integrations.stdlib import StdlibIntegration
from sentry_sdk.integrations.threading import ThreadingIntegration
from sentry_sdk.tracing import BAGGAGE_HEADER_NAME, SENTRY_TRACE_HEADER_NAME
from structlog.stdlib import get_logger

from authentik import authentik_build_hash, authentik_version
from authentik.lib.config import CONFIG
from authentik.lib.tracing.common import Tracer
from authentik.lib.tracing.exceptions import should_ignore_exception
from authentik.lib.utils.http import authentik_user_agent
from authentik.lib.utils.reflection import get_env

LOGGER = get_logger()
_root_path = CONFIG.get("web.path", "/")


class _SentryTransport(HttpTransport):
    """Custom sentry transport with custom user-agent"""

    def __init__(self, options: dict[str, Any]) -> None:
        super().__init__(options)
        self._auth = self.parsed_dsn.to_auth(authentik_user_agent())


def _traces_sampler(sampling_context: dict) -> float:
    """Custom sampler to ignore certain routes"""
    path = sampling_context.get("asgi_scope", {}).get("path", "")
    _type = sampling_context.get("asgi_scope", {}).get("type", "")
    # Ignore all healthcheck routes
    if path.startswith(f"{_root_path}-/health") or path.startswith(f"{_root_path}-/metrics"):
        return 0
    if _type == "websocket":
        return 0
    if CONFIG.get_bool("debug"):
        return 1
    return float(CONFIG.get("error_reporting.sample_rate", 0.1))


def _before_send(event: dict, hint: dict) -> dict | None:
    """Check if error is one this branch of authentik ignores, and drop it if so"""
    exc_value = None
    if "exc_info" in hint:
        _, exc_value, _ = hint["exc_info"]
        if should_ignore_exception(exc_value):
            LOGGER.debug("dropping exception", exc=exc_value)
            return None
    if event.get("logger") in [
        "asyncio",
        "multiprocessing",
        "django.security.DisallowedHost",
        "paramiko.transport",
    ]:
        return None
    LOGGER.debug("sending event to sentry", exc=exc_value, source_logger=event.get("logger", None))
    if settings.DEBUG:
        return None
    return event


class SentryTracer(Tracer):
    """Tracer backed by the Sentry SDK, reporting crashes to error_reporting.sentry_dsn"""

    def setup_pre_fork(self) -> None:
        """Configure and initialize the Sentry SDK"""
        sentry_sdk.init(
            dsn=CONFIG.get("error_reporting.sentry_dsn"),
            environment=CONFIG.get("error_reporting.environment", "customer"),
            send_default_pii=CONFIG.get_bool("error_reporting.send_pii", False),
            _experiments={
                "profiles_sample_rate": float(CONFIG.get("error_reporting.sample_rate", 0.1)),
            },
            spotlight=settings.DEBUG,
            integrations=[
                ArgvIntegration(),
                DjangoIntegration(transaction_style="function_name", cache_spans=True),
                DramatiqIntegration(),
                SocketIntegration(),
                StdlibIntegration(),
                ThreadingIntegration(propagate_hub=True),
            ],
            before_send=_before_send,
            traces_sampler=_traces_sampler,
            release=f"authentik@{authentik_version()}",
            transport=_SentryTransport,
            **CONFIG.get_dict_from_b64_json("error_reporting.extra_args", {}),
        )
        sentry_sdk.set_tag("authentik.build_hash", authentik_build_hash("tagged"))
        sentry_sdk.set_tag("authentik.env", get_env())
        sentry_sdk.set_tag("authentik.component", "backend")

    def record_exception(self, exc: Exception) -> None:
        sentry_sdk.capture_exception(exc)

    def get_http_meta(self) -> dict[str, str]:
        scope = get_current_scope()
        meta = {SENTRY_TRACE_HEADER_NAME: scope.get_traceparent() or ""}
        if bag := scope.get_baggage():
            meta[BAGGAGE_HEADER_NAME] = bag.serialize()
        return meta

    def set_tag(self, key: str, value: Any) -> None:
        sentry_sdk.set_tag(key, value)

    @contextmanager
    def active_tracer().start_span(self, op: str, name: str | None = None):
        with sentry_sdk.start_span(op=op, name=name) as span:
            yield span
