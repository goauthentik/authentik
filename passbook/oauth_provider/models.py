"""Oauth2 provider product extension"""

from django.db import models
from oauth2_provider.models import Application

from passbook.core.models import Provider


class OAuth2Provider(Provider):
    """Associate an OAuth2 Application with a Product"""

    oauth2_app = models.ForeignKey(Application, on_delete=models.CASCADE)
