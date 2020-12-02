"""OTP Time"""
from django.apps import AppConfig


class AuthentikStageOTPTimeConfig(AppConfig):
    """OTP time App config"""

    name = "authentik.stages.otp_time"
    label = "authentik_stages_otp_time"
    verbose_name = "authentik OTP.Time"
    mountpoint = "-/user/otp/time/"
