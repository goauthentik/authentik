"""passbook captcha stage"""

from django.views.generic import FormView

from passbook.flows.stage import AuthenticationStage
from passbook.stages.captcha.forms import CaptchaForm


class CaptchaStage(FormView, AuthenticationStage):
    """Simple captcha checker, logic is handeled in django-captcha module"""

    form_class = CaptchaForm

    def form_valid(self, form):
        return self.executor.stage_ok()

    def get_form(self, form_class=None):
        form = CaptchaForm(**self.get_form_kwargs())
        form.fields["captcha"].public_key = self.executor.current_stage.public_key
        form.fields["captcha"].private_key = self.executor.current_stage.private_key
        form.fields["captcha"].widget.attrs["data-sitekey"] = form.fields[
            "captcha"
        ].public_key
        return form
