"""passbook auth oidc provider app config"""
from logging import getLogger

from django.apps import AppConfig
from django.urls import include, path

LOGGER = getLogger(__name__)

class PassbookOIDCProviderConfig(AppConfig):
    """passbook auth oidc provider app config"""

    name = 'passbook.oidc_provider'
    label = 'passbook_oidc_provider'
    verbose_name = 'passbook OIDC Provider'

    def ready(self):
        from Cryptodome.PublicKey import RSA
        from oidc_provider.models import RSAKey
        if not RSAKey.objects.exists():
            key = RSA.generate(2048)
            rsakey = RSAKey(key=key.exportKey('PEM').decode('utf8'))
            rsakey.save()
            LOGGER.info("Created key")
        from passbook.root import urls
        urls.urlpatterns.append(
            path('application/oidc/', include('oidc_provider.urls', namespace='oidc_provider')),
        )
