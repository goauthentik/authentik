"""http helpers"""

from typing import TYPE_CHECKING, Any
from uuid import uuid4

from requests.models import Response
from requests.sessions import PreparedRequest, Session
from structlog.stdlib import get_logger

from authentik import authentik_full_version
from authentik.lib.config import CONFIG

if TYPE_CHECKING:
    from requests.sessions import _Timeout

LOGGER = get_logger()


def authentik_user_agent() -> str:
    """Get a common user agent"""
    return f"authentik@{authentik_full_version()}"


class TimeoutSession(Session):
    """Always set a default HTTP request timeout"""

    def __init__(self, default_timeout: int | None = None) -> None:
        super().__init__()
        self.timeout = default_timeout

    def send(
        self,
        request: PreparedRequest,
        *,
        timeout: "_Timeout | None" = None,
        **kwargs: Any,
    ) -> Response:
        if not timeout and self.timeout:
            timeout = self.timeout
        return super().send(request, timeout=timeout, **kwargs)


class DebugSession(TimeoutSession):
    """requests session which logs http requests and responses"""

    def send(
        self,
        request: PreparedRequest,
        **kwargs: Any,
    ) -> Response:
        request_id = str(uuid4())
        LOGGER.debug(
            "HTTP request sent",
            uid=request_id,
            url=request.url,
            method=request.method,
            headers=request.headers,
            body=request.body,
        )
        resp = super().send(request, **kwargs)
        LOGGER.debug(
            "HTTP response received",
            uid=request_id,
            status=resp.status_code,
            body=resp.text[: 32 * 1024],
            headers=resp.headers,
        )
        return resp


def get_http_session() -> Session:
    """Get a requests session with common headers"""
    session = TimeoutSession()
    if CONFIG.get_bool("debug") or CONFIG.get("log_level") == "trace":
        session = DebugSession()
    session.headers["User-Agent"] = authentik_user_agent()
    session.timeout = CONFIG.get_optional_int("http_timeout")
    return session
