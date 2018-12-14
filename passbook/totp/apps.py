"""passbook TOTP AppConfig"""

from django.apps.config import AppConfig


class PassbookTOTPConfig(AppConfig):
    """passbook TOTP AppConfig"""

    name = 'passbook.totp'
    label = 'passbook_totp'
    mountpoint = 'user/totp/'
