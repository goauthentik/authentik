from django.db import models

from authentik.endpoints.models import Connector


class GoogleChromeConnector(Connector):
    credentials = models.JSONField()
