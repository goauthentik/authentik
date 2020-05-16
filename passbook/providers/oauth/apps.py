"""passbook auth oauth provider app config"""

from django.apps import AppConfig


class PassbookProviderOAuthConfig(AppConfig):
    """passbook auth oauth provider app config"""

    name = "passbook.providers.oauth"
    label = "passbook_providers_oauth"
    verbose_name = "passbook Providers.OAuth"
    mountpoint = ""
