"""passbook administration forms"""
from django import forms
from django.utils.translation import gettext_lazy as _

from passbook.stages.email.models import EmailStage


class EmailStageSendForm(forms.Form):
    """Form used when sending the e-mail to prevent multiple emails being sent"""

    invalid = forms.CharField(widget=forms.HiddenInput, required=True)


class EmailStageForm(forms.ModelForm):
    """Form to create/edit E-Mail Stage"""

    class Meta:

        model = EmailStage
        fields = [
            "name",
            "host",
            "port",
            "username",
            "password",
            "use_tls",
            "use_ssl",
            "timeout",
            "from_address",
            "token_expiry",
            "subject",
            "template",
        ]
        widgets = {
            "name": forms.TextInput(),
            "host": forms.TextInput(),
            "username": forms.TextInput(),
            "password": forms.TextInput(),
        }
        labels = {
            "use_tls": _("Use TLS"),
            "use_ssl": _("Use SSL"),
        }
