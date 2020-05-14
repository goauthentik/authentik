"""http helpers"""
from typing import Any, Dict, Optional

from django.http import HttpRequest


def _get_client_ip_from_meta(meta: Dict[str, Any]) -> Optional[str]:
    """Attempt to get the client's IP by checking common HTTP Headers.
    Returns none if no IP Could be found"""
    headers = (
        "HTTP_X_FORWARDED_FOR",
        "HTTP_X_REAL_IP",
        "REMOTE_ADDR",
    )
    for _header in headers:
        if _header in meta:
            return meta.get(_header)
    return None


def get_client_ip(request: Optional[HttpRequest]) -> Optional[str]:
    """Attempt to get the client's IP by checking common HTTP Headers.
    Returns none if no IP Could be found"""
    if request:
        return _get_client_ip_from_meta(request.META)
    return ""
