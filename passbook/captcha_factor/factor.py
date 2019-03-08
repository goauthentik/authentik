"""passbook captcha factor"""

from django.views.generic import FormView

from passbook.captcha_factor.forms import CaptchaForm
from passbook.core.auth.factor import AuthenticationFactor


class CaptchaFactor(FormView, AuthenticationFactor):
    """Simple captcha checker, logic is handeled in django-captcha module"""

    form_class = CaptchaForm

    def form_valid(self, form):
        return self.authenticator.user_ok()

    def get_form(self, form_class=None):
        form = CaptchaForm(**self.get_form_kwargs())
        form.fields['captcha'].public_key = '6Lfi1w8TAAAAAELH-YiWp0OFItmMzvjGmw2xkvUN'
        form.fields['captcha'].private_key = '6Lfi1w8TAAAAAMQI3f86tGMvd1QkcqqVQyBWI23D'
        form.fields['captcha'].widget.attrs["data-sitekey"] = form.fields['captcha'].public_key
        return form
