"""passbook administration forms"""
from django import forms
from django.utils.translation import gettext_lazy as _

from passbook.flows.models import Flow, FlowDesignation
from passbook.stages.password.models import PasswordStage


def get_authentication_backends():
    """Return all available authentication backends as tuple set"""
    return [
        (
            "django.contrib.auth.backends.ModelBackend",
            _("passbook-internal Userdatabase"),
        ),
        (
            "passbook.sources.ldap.auth.LDAPBackend",
            _("passbook LDAP"),
        ),
    ]


class PasswordForm(forms.Form):
    """Password authentication form"""

    username = forms.CharField(
        widget=forms.HiddenInput(attrs={"autocomplete": "username"}), required=False
    )
    password = forms.CharField(
        label=_("Please enter your password."),
        widget=forms.PasswordInput(
            attrs={
                "placeholder": _("Password"),
                "autofocus": "autofocus",
                "autocomplete": "current-password",
            }
        ),
    )


class PasswordStageForm(forms.ModelForm):
    """Form to create/edit Password Stages"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["configure_flow"].queryset = Flow.objects.filter(
            designation=FlowDesignation.STAGE_CONFIGURATION
        )

    class Meta:

        model = PasswordStage
        fields = ["name", "backends", "configure_flow", "failed_attempts_before_cancel"]
        widgets = {
            "name": forms.TextInput(),
            "backends": forms.SelectMultiple(
                get_authentication_backends()
            ),
        }
