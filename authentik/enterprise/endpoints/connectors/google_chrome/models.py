from django.db import models
from google.oauth2.service_account import Credentials

from authentik.endpoints.models import Connector


class GoogleChromeConnector(Connector):
    credentials = models.JSONField()

    def google_credentials(self):
        return {
            "credentials": Credentials.from_service_account_info(
                self.credentials, scopes=["https://www.googleapis.com/auth/verifiedaccess"]
            ),
        }
