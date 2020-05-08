"""passbook administration forms"""
from django import forms
from django.utils.translation import gettext_lazy as _

from passbook.stages.email.models import EmailStage


class EmailStageForm(forms.ModelForm):
    """Form to create/edit Dummy Stage"""

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
            "ssl_keyfile",
            "ssl_certfile",
        ]
        widgets = {
            "name": forms.TextInput(),
            "host": forms.TextInput(),
            "username": forms.TextInput(),
            "password": forms.TextInput(),
            "ssl_keyfile": forms.TextInput(),
            "ssl_certfile": forms.TextInput(),
        }
        labels = {
            "use_tls": _("Use TLS"),
            "use_ssl": _("Use SSL"),
            "ssl_keyfile": _("SSL Keyfile (optional)"),
            "ssl_certfile": _("SSL Certfile (optional)"),
        }
