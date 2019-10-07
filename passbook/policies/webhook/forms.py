"""passbook Policy forms"""

from django import forms

from passbook.policies.forms import GENERAL_FIELDS
from passbook.policies.webhook.models import WebhookPolicy


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
