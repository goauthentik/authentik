"""passbook rule forms"""

from django import forms

from passbook.core.models import FieldMatcherRule, WebhookRule


class FieldMatcherRuleForm(forms.ModelForm):
    """FieldMatcherRule Form"""

    class Meta:

        model = FieldMatcherRule
        fields = ['name', 'action', 'negate', 'order',
                  'user_field', 'match_action', 'value', ]
        widgets = {
            'name': forms.TextInput(),
            'user_field': forms.TextInput(),
            'value': forms.TextInput(),
        }


class WebhookRuleForm(forms.ModelForm):
    """WebhookRuleForm Form"""

    class Meta:

        model = WebhookRule
        fields = ['url', 'method', 'json_body', 'json_headers',
                  'result_jsonpath', 'result_json_value', ]
        widgets = {
            'json_body': forms.TextInput(),
            'json_headers': forms.TextInput(),
            'result_jsonpath': forms.TextInput(),
            'result_json_value': forms.TextInput(),
        }
