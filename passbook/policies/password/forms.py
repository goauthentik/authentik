"""passbook Policy forms"""

from django import forms
from django.utils.translation import gettext as _

from passbook.policies.forms import GENERAL_FIELDS
from passbook.policies.password.models import PasswordPolicy


class PasswordPolicyForm(forms.ModelForm):
    """PasswordPolicy Form"""

    class Meta:

        model = PasswordPolicy
        fields = GENERAL_FIELDS + ['amount_uppercase', 'amount_lowercase',
                                   'amount_symbols', 'length_min', 'symbol_charset',
                                   'error_message']
        widgets = {
            'name': forms.TextInput(),
            'symbol_charset': forms.TextInput(),
            'error_message': forms.TextInput(),
        }
        labels = {
            'amount_uppercase': _('Minimum amount of Uppercase Characters'),
            'amount_lowercase': _('Minimum amount of Lowercase Characters'),
            'amount_symbols': _('Minimum amount of Symbols Characters'),
            'length_min': _('Minimum Length'),
        }
