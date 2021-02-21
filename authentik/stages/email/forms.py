"""authentik administration forms"""
from django import forms
from django.utils.translation import gettext_lazy as _

from authentik.stages.email.models import EmailStage, get_template_choices


class EmailStageForm(forms.ModelForm):
    """Form to create/edit Email Stage"""

    template = forms.ChoiceField(choices=get_template_choices)

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
