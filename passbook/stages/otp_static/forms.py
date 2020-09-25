"""OTP Static forms"""
from django import forms
from django.utils.safestring import mark_safe

from passbook.stages.otp_static.models import OTPStaticStage


class StaticTokenWidget(forms.widgets.Widget):
    """Widget to render tokens as multiple labels"""

    def render(self, name, value, attrs=None, renderer=None):
        final_string = '<ul class="pb-otp-tokens">'
        for token in value:
            final_string += f"<li>{token.token}</li>"
        final_string += "</ul>"
        return mark_safe(final_string)  # nosec


class SetupForm(forms.Form):
    """Form to setup Static OTP"""

    tokens = forms.CharField(widget=StaticTokenWidget, disabled=True, required=False)

    def __init__(self, tokens, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tokens"].initial = tokens


class OTPStaticStageForm(forms.ModelForm):
    """OTP Static Stage setup form"""

    class Meta:

        model = OTPStaticStage
        fields = ["name", "configure_flow", "token_count"]

        widgets = {
            "name": forms.TextInput(),
        }
