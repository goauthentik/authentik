import django.conf


class OTPEmailSettings:
    """
    This is a simple class to take the place of the global settings object.

    An instance will contain all of our settings as attributes, with default
    values if they are not specified by the configuration.

    """

    defaults = {
        "OTP_EMAIL_SENDER": None,
        "OTP_EMAIL_SUBJECT": "OTP token",
        "OTP_EMAIL_BODY_TEMPLATE": None,
        "OTP_EMAIL_BODY_TEMPLATE_PATH": "otp/email/token.txt",
        "OTP_EMAIL_BODY_HTML_TEMPLATE": None,
        "OTP_EMAIL_BODY_HTML_TEMPLATE_PATH": None,
        "OTP_EMAIL_TOKEN_VALIDITY": 300,
        "OTP_EMAIL_THROTTLE_FACTOR": 1,
    }

    def __getattr__(self, name):
        if name in self.defaults:
            return getattr(django.conf.settings, name, self.defaults[name])
        else:
            return getattr(django.conf.settings, name)


settings = OTPEmailSettings()
