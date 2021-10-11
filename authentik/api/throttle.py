"""Throttling classes"""
from typing import Type

from django.views import View
from rest_framework.request import Request
from rest_framework.throttling import ScopedRateThrottle


class SessionThrottle(ScopedRateThrottle):
    """Throttle based on session key"""

    def allow_request(self, request: Request, view):
        if request._request.user.is_superuser:
            return True
        return super().allow_request(request, view)

    def get_cache_key(self, request: Request, view: Type[View]) -> str:
        return f"authentik-throttle-session-{request._request.session.session_key}"
