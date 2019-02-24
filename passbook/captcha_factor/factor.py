"""passbook captcha factor"""

from django.views.generic import FormView

from passbook.captcha_factor.forms import CaptchaForm
from passbook.core.auth.factor import AuthenticationFactor


class CaptchaFactor(FormView, AuthenticationFactor):
    """Simple captcha checker, logic is handeled in django-captcha module"""

    form_class = CaptchaForm

    def form_valid(self, form):
        return self.authenticator.user_ok()
