"""OTP Validation Stage"""
from django.apps import AppConfig


class AuthentikStageOTPValidateConfig(AppConfig):
    """OTP Validation Stage"""

    name = "authentik.stages.otp_validate"
    label = "authentik_stages_otp_validate"
    verbose_name = "authentik OTP.Validate"
