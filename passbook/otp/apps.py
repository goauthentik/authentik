"""passbook OTP AppConfig"""

from django.apps.config import AppConfig


class PassbookOTPConfig(AppConfig):
    """passbook OTP AppConfig"""

    name = 'passbook.otp'
    label = 'passbook_otp'
    verbose_name = 'passbook OTP'
    mountpoint = 'user/otp/'
