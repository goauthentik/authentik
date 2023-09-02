import django.conf
from django.utils.functional import cached_property


class Settings:
    """
    This is a simple class to take the place of the global settings object. An
    instance will contain all of our settings as attributes, with default values
    if they are not specified by the configuration.
    """

    @cached_property
    def defaults(self):
        return {
            "OTP_LOGIN_URL": django.conf.settings.LOGIN_URL,
            "OTP_ADMIN_HIDE_SENSITIVE_DATA": False,
        }

    def __getattr__(self, name):
        if name in self.defaults:
            return getattr(django.conf.settings, name, self.defaults[name])
        else:
            return getattr(django.conf.settings, name)


settings = Settings()
