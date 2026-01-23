"""Endpoint stage"""

from typing import TYPE_CHECKING

from django.db import models
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from google.oauth2.service_account import Credentials
from rest_framework.serializers import BaseSerializer

from authentik.endpoints.models import Connector
from authentik.flows.stage import StageView

if TYPE_CHECKING:
    from authentik.enterprise.endpoints.connectors.google_chrome.controller import (
        GoogleChromeController,
    )


class GoogleChromeConnector(Connector):
    """Verify Google Chrome Device Trust connection for the user's browser."""

    credentials = models.JSONField()

    def google_credentials(self):
        return {
            "credentials": Credentials.from_service_account_info(
                self.credentials, scopes=["https://www.googleapis.com/auth/verifiedaccess"]
            ),
        }

    @property
    def icon_url(self):
        return static("authentik/sources/google.svg")

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.enterprise.stages.authenticator_endpoint_gdtc.api import (
            AuthenticatorEndpointGDTCStageSerializer,
        )

        return AuthenticatorEndpointGDTCStageSerializer

    @property
    def stage(self) -> type[StageView] | None:
        from authentik.enterprise.endpoints.connectors.google_chrome.stage import (
            GoogleChromeStageView,
        )

        return GoogleChromeStageView

    @property
    def controller(self) -> type[GoogleChromeController]:
        from authentik.enterprise.endpoints.connectors.google_chrome.controller import (
            GoogleChromeController,
        )

        return GoogleChromeController

    @property
    def component(self) -> str:
        return "ak-stage-authenticator-endpoint-gdtc-form"

    def __str__(self) -> str:
        return f"Endpoint Authenticator Google Device Trust Connector Stage {self.name}"

    class Meta:
        verbose_name = _("Endpoint Authenticator Google Device Trust Connector Stage")
        verbose_name_plural = _("Endpoint Authenticator Google Device Trust Connector Stages")
