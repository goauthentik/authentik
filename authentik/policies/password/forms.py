"""authentik Policy forms"""

from django import forms
from django.utils.translation import gettext as _

from authentik.policies.forms import PolicyForm
from authentik.policies.password.models import PasswordPolicy


class PasswordPolicyForm(PolicyForm):
    """PasswordPolicy Form"""

    class Meta:

        model = PasswordPolicy
        fields = PolicyForm.Meta.fields + [
            "password_field",
            "amount_uppercase",
            "amount_lowercase",
            "amount_symbols",
            "length_min",
            "symbol_charset",
            "error_message",
        ]
        widgets = {
            "name": forms.TextInput(),
            "password_field": forms.TextInput(),
            "symbol_charset": forms.TextInput(),
            "error_message": forms.TextInput(),
        }
        labels = {
            "amount_uppercase": _("Minimum amount of Uppercase Characters"),
            "amount_lowercase": _("Minimum amount of Lowercase Characters"),
            "amount_symbols": _("Minimum amount of Symbols Characters"),
            "length_min": _("Minimum Length"),
        }
