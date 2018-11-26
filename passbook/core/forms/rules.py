"""passbook rule forms"""

from django import forms

from passbook.core.models import FieldMatcherRule


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
