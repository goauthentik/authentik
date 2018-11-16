"""passbook 2FA AppConfig"""

from django.apps.config import AppConfig


class PassbookTFAConfig(AppConfig):
    """passbook TFA AppConfig"""

    name = 'passbook.tfa'
    label = 'passbook_tfa'
