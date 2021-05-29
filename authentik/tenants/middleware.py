"""Inject tenant into current request"""
from typing import Callable

from django.http.request import HttpRequest
from django.http.response import HttpResponse

from authentik.tenants.utils import get_tenant_for_request


class TenantMiddleware:
    """Add current tenant to http request"""

    get_response: Callable[[HttpRequest], HttpResponse]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not hasattr(request, "tenant"):
            tenant = get_tenant_for_request(request)
            setattr(request, "tenant", tenant)
        return self.get_response(request)
