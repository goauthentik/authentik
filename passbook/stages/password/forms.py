"""passbook administration forms"""
from django import forms
from django.conf import settings
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _

from passbook.lib.utils.reflection import path_to_class
from passbook.stages.password.models import PasswordStage


def get_authentication_backends():
    """Return all available authentication backends as tuple set"""
    for backend in settings.AUTHENTICATION_BACKENDS:
        klass = path_to_class(backend)
        yield backend, getattr(
            klass(), "name", "%s (%s)" % (klass.__name__, klass.__module__)
        )


class PasswordForm(forms.Form):
    """Password authentication form"""

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
