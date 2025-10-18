from django.db import models
from google.oauth2.service_account import Credentials
from rest_framework.serializers import Serializer

from authentik.endpoints.models import Connector
from authentik.flows.stage import StageView


class GoogleChromeConnector(Connector):
    credentials = models.JSONField()

    def google_credentials(self):
        return {
            "credentials": Credentials.from_service_account_info(
                self.credentials, scopes=["https://www.googleapis.com/auth/verifiedaccess"]
            ),
        }

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.endpoints.connectors.google_chrome.api import (
            GoogleChromeConnectorSerializer,
        )

        return GoogleChromeConnectorSerializer

    @property
    def stage(self) -> type[StageView] | None:
        from authentik.enterprise.endpoints.connectors.google_chrome.stage import (
            AuthenticatorEndpointStageView,
        )

        return AuthenticatorEndpointStageView
