"""passbook OTP AppConfig"""

from django.apps.config import AppConfig


class PassbookStageOTPConfig(AppConfig):
    """passbook OTP AppConfig"""

    name = "passbook.stages.otp"
    label = "passbook_stages_otp"
    verbose_name = "passbook Stages.OTP"
    mountpoint = "user/otp/"
