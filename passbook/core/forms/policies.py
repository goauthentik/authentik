"""passbook Policy forms"""

from django import forms
from django.utils.translation import gettext as _

from passbook.core.models import (DebugPolicy, FieldMatcherPolicy,
                                  GroupMembershipPolicy, PasswordPolicy,
                                  WebhookPolicy)

GENERAL_FIELDS = ['name', 'action', 'negate', 'order', 'timeout']

class FieldMatcherPolicyForm(forms.ModelForm):
    """FieldMatcherPolicy Form"""

    class Meta:

        model = FieldMatcherPolicy
        fields = GENERAL_FIELDS + ['user_field', 'match_action', 'value', ]
        widgets = {
            'name': forms.TextInput(),
            'value': forms.TextInput(),
        }


class WebhookPolicyForm(forms.ModelForm):
    """WebhookPolicyForm Form"""

    class Meta:

        model = WebhookPolicy
        fields = GENERAL_FIELDS + ['url', 'method', 'json_body', 'json_headers',
                                   'result_jsonpath', 'result_json_value', ]
        widgets = {
            'name': forms.TextInput(),
            'json_body': forms.TextInput(),
            'json_headers': forms.TextInput(),
            'result_jsonpath': forms.TextInput(),
            'result_json_value': forms.TextInput(),
        }


class DebugPolicyForm(forms.ModelForm):
    """DebugPolicyForm Form"""

    class Meta:

        model = DebugPolicy
        fields = GENERAL_FIELDS + ['result', 'wait_min', 'wait_max']
        widgets = {
            'name': forms.TextInput(),
        }
        labels = {
            'result': _('Allow user')
        }


class GroupMembershipPolicyForm(forms.ModelForm):
    """GroupMembershipPolicy Form"""

    class Meta:

        model = GroupMembershipPolicy
        fields = GENERAL_FIELDS + ['group', ]
        widgets = {
            'name': forms.TextInput(),
        }

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
