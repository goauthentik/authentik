"""General fields"""
from django import forms

from passbook.policies.models import PolicyBinding, PolicyBindingModel

GENERAL_FIELDS = ["name", "negate", "order", "timeout"]
GENERAL_SERIALIZER_FIELDS = ["pk", "name", "negate", "order", "timeout"]


class PolicyBindingForm(forms.ModelForm):
    """Form to edit Policy to PolicyBindingModel Binding"""

    target = forms.ModelChoiceField(
        queryset=PolicyBindingModel.objects.all().select_subclasses(),
        to_field_name="pbm_uuid",
    )

    class Meta:

        model = PolicyBinding
        fields = [
            "enabled",
            "policy",
            "target",
            "order",
        ]
