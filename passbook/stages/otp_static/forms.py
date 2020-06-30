"""OTP Static forms"""
from django import forms

from passbook.stages.otp_static.models import OTPStaticStage


class SetupForm(forms.Form):
    """Form to setup Static OTP"""

    tokens = forms.MultipleChoiceField(disabled=True, required=False)

    def __init__(self, tokens, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(tokens)
        self.fields["tokens"].choices = [(x.token, x.token) for x in tokens]


class OTPStaticStageForm(forms.ModelForm):
    """OTP Static Stage setup form"""

    class Meta:

        model = OTPStaticStage
        fields = ["name", "token_count"]

        widgets = {
            "name": forms.TextInput(),
        }
