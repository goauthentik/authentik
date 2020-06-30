"""OTP Validation Stage"""
from django.apps import AppConfig


class PassbookStageOTPValidateConfig(AppConfig):
    """OTP Validation Stage"""

    name = "passbook.stages.otp_validate"
    label = "passbook_stages_otp_validate"
    verbose_name = "passbook OTP.Validate"
