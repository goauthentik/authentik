"""General fields"""

from django import forms

from authentik.lib.widgets import GroupedModelChoiceField
from authentik.policies.models import Policy, PolicyBinding, PolicyBindingModel

GENERAL_FIELDS = ["name"]
GENERAL_SERIALIZER_FIELDS = ["pk", "name"]


class PolicyBindingForm(forms.ModelForm):
    """Form to edit Policy to PolicyBindingModel Binding"""

    target = GroupedModelChoiceField(
        queryset=PolicyBindingModel.objects.all().select_subclasses(),
        to_field_name="pbm_uuid",
    )
    policy = GroupedModelChoiceField(
        queryset=Policy.objects.all().select_subclasses(),
    )

    class Meta:

        model = PolicyBinding
        fields = ["enabled", "policy", "target", "order", "timeout"]
