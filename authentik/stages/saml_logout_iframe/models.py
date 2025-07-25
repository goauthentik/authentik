"""SAML iframe logout stage models"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Stage


class SAMLIframeLogoutStage(Stage):
    """Stage that handles SAML logout using iframes for providers that don't support redirects"""

    iframe_timeout = models.IntegerField(
        default=5000,
        help_text=_("Timeout in milliseconds to wait for each iframe to load"),
    )

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.saml_logout_iframe.api import SAMLIframeLogoutStageSerializer

        return SAMLIframeLogoutStageSerializer

    @property
    def view(self) -> type[View]:
        from authentik.stages.saml_logout_iframe.stage import SAMLIframeLogoutStageView

        return SAMLIframeLogoutStageView

    @property
    def component(self) -> str:
        return "ak-stage-saml-iframe-logout-form"

    class Meta:
        verbose_name = _("SAML Iframe Logout Stage")
        verbose_name_plural = _("SAML Iframe Logout Stages")
