"""passbook rule forms"""

from django import forms
from django.utils.translation import gettext as _

from passbook.core.models import DebugRule, FieldMatcherRule, WebhookRule

GENERAL_FIELDS = ['name', 'action', 'negate', 'order', ]

class FieldMatcherRuleForm(forms.ModelForm):
    """FieldMatcherRule Form"""

    class Meta:

        model = FieldMatcherRule
        fields = GENERAL_FIELDS + ['user_field', 'match_action', 'value', ]
        widgets = {
            'name': forms.TextInput(),
            'value': forms.TextInput(),
        }


class WebhookRuleForm(forms.ModelForm):
    """WebhookRuleForm Form"""

    class Meta:

        model = WebhookRule
        fields = GENERAL_FIELDS + ['url', 'method', 'json_body', 'json_headers',
                                   'result_jsonpath', 'result_json_value', ]
        widgets = {
            'name': forms.TextInput(),
            'json_body': forms.TextInput(),
            'json_headers': forms.TextInput(),
            'result_jsonpath': forms.TextInput(),
            'result_json_value': forms.TextInput(),
        }


class DebugRuleForm(forms.ModelForm):
    """DebugRuleForm Form"""

    class Meta:

        model = DebugRule
        fields = GENERAL_FIELDS + ['result', 'wait_min', 'wait_max']
        widgets = {
            'name': forms.TextInput(),
        }
        labels = {
            'result': _('Allow user')
        }
