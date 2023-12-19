"""http helpers"""
from typing import Optional

from django.http import HttpRequest
from requests.sessions import Session
from structlog.stdlib import get_logger

from authentik import get_full_version

LOGGER = get_logger()


def get_client_ip(request: Optional[HttpRequest]) -> str:
    """Attempt to get the client's IP by checking common HTTP Headers.
    Returns none if no IP Could be found"""
    from authentik.root.middleware import ClientIPMiddleware

    return ClientIPMiddleware.get_client_ip(request)


def authentik_user_agent() -> str:
    """Get a common user agent"""
    return f"authentik@{get_full_version()}"


def get_http_session() -> Session:
    """Get a requests session with common headers"""
    session = Session()
    session.headers["User-Agent"] = authentik_user_agent()
    return session
