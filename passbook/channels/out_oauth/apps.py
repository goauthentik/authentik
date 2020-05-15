"""passbook auth oauth provider app config"""

from django.apps import AppConfig


class PassbookOutletOAuthConfig(AppConfig):
    """passbook auth oauth provider app config"""

    name = "passbook.channels.out_oauth"
    label = "passbook_channels_out_oauth"
    verbose_name = "passbook Outlets.OAuth"
    mountpoint = ""
