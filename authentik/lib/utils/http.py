"""http helpers"""

from uuid import uuid4

from requests.sessions import PreparedRequest, Session
from structlog.stdlib import get_logger

from authentik import get_full_version
from authentik.lib.config import CONFIG

LOGGER = get_logger()


def authentik_user_agent() -> str:
    """Get a common user agent"""
    return f"authentik@{get_full_version()}"


class DebugSession(Session):
    """requests session which logs http requests and responses"""

    def send(self, req: PreparedRequest, *args, **kwargs):
        request_id = str(uuid4())
        LOGGER.debug(
            "HTTP request sent",
            uid=request_id,
            url=req.url,
            method=req.method,
            headers=req.headers,
            body=req.body,
        )
        resp = super().send(req, *args, **kwargs)
        LOGGER.debug(
            "HTTP response received",
            uid=request_id,
            status=resp.status_code,
            body=resp.text,
            headers=resp.headers,
        )
        return resp


def get_http_session() -> Session:
    """Get a requests session with common headers"""
    session = Session()
    if CONFIG.get_bool("debug") or CONFIG.get("log_level") == "trace":
        session = DebugSession()
    session.headers["User-Agent"] = authentik_user_agent()
    return session
