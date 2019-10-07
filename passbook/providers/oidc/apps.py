"""passbook auth oidc provider app config"""
from django.apps import AppConfig
from django.db.utils import InternalError, OperationalError, ProgrammingError
from django.urls import include, path
from structlog import get_logger

LOGGER = get_logger()

class PassbookProviderOIDCConfig(AppConfig):
    """passbook auth oidc provider app config"""

    name = 'passbook.providers.oidc'
    label = 'passbook_providers_oidc'
    verbose_name = 'passbook Providers.OIDC'

    def ready(self):
        try:
            from Cryptodome.PublicKey import RSA
            from oidc_provider.models import RSAKey
            if not RSAKey.objects.exists():
                key = RSA.generate(2048)
                rsakey = RSAKey(key=key.exportKey('PEM').decode('utf8'))
                rsakey.save()
                LOGGER.info("Created key")
        except (OperationalError, ProgrammingError, InternalError):
            pass
        from passbook.root import urls
        urls.urlpatterns.append(
            path('application/oidc/', include('oidc_provider.urls', namespace='oidc_provider')),
        )
