"""passbook administration forms"""
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _

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
            _("passbook LDAP (Only needed when User-Sync is not enabled."),
        ),
    ]


class PasswordForm(forms.Form):
    """Password authentication form"""

    username = forms.CharField(
        widget=forms.HiddenInput(attrs={"autocomplete": "username"}), required=False
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": _("Password"),
                "autofocus": "autofocus",
                "autocomplete": "current-password",
            }
        )
    )


class PasswordStageForm(forms.ModelForm):
    """Form to create/edit Password Stages"""

    class Meta:

        model = PasswordStage
        fields = ["name", "backends"]
        widgets = {
            "name": forms.TextInput(),
            "backends": FilteredSelectMultiple(
                _("backends"), False, choices=get_authentication_backends()
            ),
            "password_policies": FilteredSelectMultiple(_("password policies"), False),
        }
