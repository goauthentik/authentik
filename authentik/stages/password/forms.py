"""authentik administration forms"""
from django import forms
from django.utils.translation import gettext_lazy as _

from authentik.flows.models import Flow, FlowDesignation
from authentik.stages.password.models import PasswordStage


def get_authentication_backends():
    """Return all available authentication backends as tuple set"""
    return [
        (
            "django.contrib.auth.backends.ModelBackend",
            _("authentik-internal Userdatabase"),
        ),
        (
            "authentik.sources.ldap.auth.LDAPBackend",
            _("authentik LDAP"),
        ),
    ]


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
            "backends": forms.SelectMultiple(choices=get_authentication_backends()),
        }
