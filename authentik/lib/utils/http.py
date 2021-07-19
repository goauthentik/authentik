"""http helpers"""
from typing import Any, Optional

from django.http import HttpRequest
from structlog.stdlib import get_logger

OUTPOST_REMOTE_IP_HEADER = "HTTP_X_AUTHENTIK_REMOTE_IP"
OUTPOST_TOKEN_HEADER = "HTTP_X_AUTHENTIK_OUTPOST_TOKEN"  # nosec
DEFAULT_IP = "255.255.255.255"
LOGGER = get_logger()


def _get_client_ip_from_meta(meta: dict[str, Any]) -> str:
    """Attempt to get the client's IP by checking common HTTP Headers.
    Returns none if no IP Could be found"""
    headers = (
        "HTTP_X_FORWARDED_FOR",
        "HTTP_X_REAL_IP",
        "REMOTE_ADDR",
    )
    for _header in headers:
        if _header in meta:
            ips: list[str] = meta.get(_header).split(",")
            return ips[0].strip()
    return DEFAULT_IP


def _get_outpost_override_ip(request: HttpRequest) -> Optional[str]:
    """Get the actual remote IP when set by an outpost. Only
    allowed when the request is authenticated, by a user with USER_ATTRIBUTE_CAN_OVERRIDE_IP set
    to outpost"""
    from authentik.core.models import (
        USER_ATTRIBUTE_CAN_OVERRIDE_IP,
        Token,
        TokenIntents,
    )

    if (
        OUTPOST_REMOTE_IP_HEADER not in request.META
        or OUTPOST_TOKEN_HEADER not in request.META
    ):
        return None
    tokens = Token.filter_not_expired(
        key=request.META.get(OUTPOST_TOKEN_HEADER), intent=TokenIntents.INTENT_API
    )
    if not tokens.exists():
        LOGGER.warning("Attempted remote-ip override without token")
        return None
    user = tokens.first().user
    if user.group_attributes().get(USER_ATTRIBUTE_CAN_OVERRIDE_IP, False):
        return None
    return request.META[OUTPOST_REMOTE_IP_HEADER]


def get_client_ip(request: Optional[HttpRequest]) -> str:
    """Attempt to get the client's IP by checking common HTTP Headers.
    Returns none if no IP Could be found"""
    if request:
        override = _get_outpost_override_ip(request)
        if override:
            return override
        return _get_client_ip_from_meta(request.META)
    return DEFAULT_IP
