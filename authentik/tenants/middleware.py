"""Inject tenant into current request"""
from typing import Callable

from django.http import HttpRequest, HttpResponse
from django_tenants.utils import get_tenant
from sentry_sdk.api import set_tag


class CurrentTenantMiddleware:
    """Add current tenant to http request"""

    get_response: Callable[[HttpRequest], HttpResponse]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not hasattr(request, "tenant"):
            tenant = get_tenant(request)
            setattr(request, "tenant", tenant)
            if tenant is not None:
                set_tag("authentik.tenant_uuid", tenant.tenant_uuid.hex)
                set_tag("authentik.tenant_domain_regex", tenant.domain_regex)
        return self.get_response(request)
