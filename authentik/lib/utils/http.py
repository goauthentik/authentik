"""http helpers"""
from requests.sessions import Session
from structlog.stdlib import get_logger

from authentik import get_full_version

LOGGER = get_logger()


def authentik_user_agent() -> str:
    """Get a common user agent"""
    return f"authentik@{get_full_version()}"


def get_http_session() -> Session:
    """Get a requests session with common headers"""
    session = Session()
    session.headers["User-Agent"] = authentik_user_agent()
    return session
