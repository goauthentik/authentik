"""SAML base views"""
from typing import Optional

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View

from passbook.core.models import Application
from passbook.policies.mixins import PolicyAccessMixin
from passbook.providers.samlv2.saml.constants import SESSION_KEY
from passbook.providers.samlv2.saml.parser import SAMLRequest


class BaseSAMLView(PolicyAccessMixin, View):
    """Base SAML View to resolve app_slug"""

    application: Application

    def setup(self, request: HttpRequest, *args, **kwargs):
        View.setup(self, request, *args, **kwargs)
        self.application = self.get_application(self.kwargs.get("app_slug"))

    def get_application(self, app_slug: str) -> Optional[Application]:
        """Return application or raise 404"""
        return get_object_or_404(Application, slug=app_slug)

    def handle_saml_request(self, request: SAMLRequest) -> HttpResponse:
        """Handle SAML Request"""
        self.request.SESSION[SESSION_KEY] = request
        if self.application.skip_authorization:
            pass
