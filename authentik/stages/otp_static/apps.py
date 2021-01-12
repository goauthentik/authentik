"""OTP Static stage"""
from django.apps import AppConfig


class AuthentikStageOTPStaticConfig(AppConfig):
    """OTP Static stage"""

    name = "authentik.stages.otp_static"
    label = "authentik_stages_otp_static"
    verbose_name = "authentik Stages.OTP.Static"
    mountpoint = "-/user/otp/static/"
