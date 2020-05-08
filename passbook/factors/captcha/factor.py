"""passbook captcha factor"""

from django.views.generic import FormView

from passbook.factors.captcha.forms import CaptchaForm
from passbook.flows.factor_base import AuthenticationFactor


class CaptchaFactor(FormView, AuthenticationFactor):
    """Simple captcha checker, logic is handeled in django-captcha module"""

    form_class = CaptchaForm

    def form_valid(self, form):
        return self.executor.factor_ok()

    def get_form(self, form_class=None):
        form = CaptchaForm(**self.get_form_kwargs())
        form.fields["captcha"].public_key = self.executor.current_factor.public_key
        form.fields["captcha"].private_key = self.executor.current_factor.private_key
        form.fields["captcha"].widget.attrs["data-sitekey"] = form.fields[
            "captcha"
        ].public_key
        return form
