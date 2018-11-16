"""Oauth2 provider product extension"""

from django.db import models
from oauth2_provider.models import Application as _OAuth2Application

from passbook.core.models import Application


class OAuth2Application(Application):
    """Associate an OAuth2 Application with a Product"""

    oauth2 = models.ForeignKey(_OAuth2Application, on_delete=models.CASCADE)
