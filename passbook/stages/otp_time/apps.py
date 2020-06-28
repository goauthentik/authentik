from django.apps import AppConfig


class PassbookStageOTPTimeConfig(AppConfig):

    name = "passbook.stages.otp_time"
    label = "passbook_stages_otp_time"
    verbose_name = "passbook OTP.Time"
    mountpoint = "-/user/otp/time/"
