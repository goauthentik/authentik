"""passbook OTP AppConfig"""

from django.apps.config import AppConfig


class PassbookFactorOTPConfig(AppConfig):
    """passbook OTP AppConfig"""

    name = 'passbook.factors.otp'
    label = 'passbook_factors_otp'
    verbose_name = 'passbook Factors.OTP'
    mountpoint = 'user/otp/'
