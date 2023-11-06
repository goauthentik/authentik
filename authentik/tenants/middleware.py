"""Inject tenant into current request"""
from typing import Callable

from django.http import HttpRequest, HttpResponse
from sentry_sdk.api import set_tag

from authentik.tenants.utils import get_tenant_for_request


class CurrentTenantMiddleware:
    """Add current tenant to http request"""

    get_response: Callable[[HttpRequest], HttpResponse]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not hasattr(request, "tenant"):
            tenant = get_tenant_for_request(request)
            setattr(request, "tenant", tenant)
            set_tag("authentik.tenant_uuid", tenant.tenant_uuid.hex)
            set_tag("authentik.tenant_domain_regex", tenant.domain_regex)
        return self.get_response(request)
