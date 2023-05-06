"""Inject tenant into current request"""
from typing import Callable

from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.utils.translation import activate
from sentry_sdk.api import set_tag

from authentik.tenants.utils import lookup_tenant_for_request


class TenantMiddleware:
    """Add current tenant to http request"""

    get_response: Callable[[HttpRequest], HttpResponse]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not hasattr(request, "tenant"):
            tenant = lookup_tenant_for_request(request)
            setattr(request, "tenant", tenant)
            set_tag("authentik.tenant_uuid", tenant.tenant_uuid.hex)
            set_tag("authentik.tenant_domain", tenant.domain)
            locale = tenant.default_locale
            if locale != "":
                activate(locale)
        return self.get_response(request)
