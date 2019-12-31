"""passbook Policy forms"""

from django import forms

from passbook.policies.forms import GENERAL_FIELDS
from passbook.policies.matcher.models import FieldMatcherPolicy


class FieldMatcherPolicyForm(forms.ModelForm):
    """FieldMatcherPolicy Form"""

    class Meta:

        model = FieldMatcherPolicy
        fields = GENERAL_FIELDS + [
            "user_field",
            "match_action",
            "value",
        ]
        widgets = {
            "name": forms.TextInput(),
            "value": forms.TextInput(),
        }
