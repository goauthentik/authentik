"""General fields"""

from django import forms

from authentik.core.models import Group
from authentik.lib.widgets import GroupedModelChoiceField
from authentik.policies.models import Policy, PolicyBinding, PolicyBindingModel

GENERAL_FIELDS = ["name", "execution_logging"]
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
    group = forms.ModelChoiceField(
        queryset=Group.objects.all().order_by("name"), required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "target" in self.initial:
            self.fields["target"].widget = forms.HiddenInput()

    class Meta:

        model = PolicyBinding
        fields = ["enabled", "policy", "target", "order", "timeout"]
