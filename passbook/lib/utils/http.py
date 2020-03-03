"""http helpers"""
from typing import Any, Dict, Optional

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, reverse
from django.utils.http import urlencode


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


def get_client_ip(request: HttpRequest) -> Optional[str]:
    """Attempt to get the client's IP by checking common HTTP Headers.
    Returns none if no IP Could be found"""
    return _get_client_ip_from_meta(request.META)


def redirect_with_qs(view: str, get_query_set=None) -> HttpResponse:
    """Wrapper to redirect whilst keeping GET Parameters"""
    # TODO: Check if URL is relative/absolute
    target = reverse(view)
    if get_query_set:
        target += "?" + urlencode(get_query_set.items())
    return redirect(target)
