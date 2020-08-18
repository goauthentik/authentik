"""passbook auth oauth provider app config"""
from django.apps import AppConfig


class PassbookProviderOAuth2Config(AppConfig):
    """passbook auth oauth provider app config"""

    name = "passbook.providers.oauth2"
    label = "passbook_providers_oauth2"
    verbose_name = "passbook Providers.OAuth2"
    mountpoints = {
        "passbook.providers.oauth2.urls": "application/o/",
        "passbook.providers.oauth2.urls_github": "",
    }
