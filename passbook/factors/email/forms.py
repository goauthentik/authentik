"""passbook administration forms"""
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext as _

from passbook.factors.email.models import EmailFactor
from passbook.factors.forms import GENERAL_FIELDS


class EmailFactorForm(forms.ModelForm):
    """Form to create/edit Dummy Factor"""

    class Meta:

        model = EmailFactor
        fields = GENERAL_FIELDS + [
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
            "order": forms.NumberInput(),
            "policies": FilteredSelectMultiple(_("policies"), False),
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
