"""authentik administration forms"""
from django import forms
from django.utils.translation import gettext_lazy as _

from authentik.stages.email.models import EmailStage, get_template_choices


class EmailStageSendForm(forms.Form):
    """Form used when sending the email to prevent multiple emails being sent"""

    invalid = forms.CharField(widget=forms.HiddenInput, required=True)


class EmailStageForm(forms.ModelForm):
    """Form to create/edit Email Stage"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["template"].choices = get_template_choices()

    class Meta:

        model = EmailStage
        fields = [
            "name",
            "use_global_settings",
            "token_expiry",
            "subject",
            "template",
            "host",
            "port",
            "username",
            "password",
            "use_tls",
            "use_ssl",
            "timeout",
            "from_address",
        ]
        widgets = {
            "name": forms.TextInput(),
            "host": forms.TextInput(),
            "subject": forms.TextInput(),
            "username": forms.TextInput(),
            "password": forms.TextInput(),
        }
        labels = {
            "use_tls": _("Use TLS"),
            "use_ssl": _("Use SSL"),
        }
