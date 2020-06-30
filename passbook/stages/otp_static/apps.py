"""OTP Static stage"""
from django.apps import AppConfig


class PassbookStageOTPStaticConfig(AppConfig):
    """OTP Static stage"""

    name = "passbook.stages.otp_static"
    label = "passbook_stages_otp_static"
    verbose_name = "passbook OTP.Static"
    mountpoint = "-/user/otp/static/"
