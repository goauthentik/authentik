"""General fields"""

from django import forms

from authentik.lib.widgets import GroupedModelChoiceField
from authentik.policies.models import Policy, PolicyBinding, PolicyBindingModel


class PolicyBindingForm(forms.ModelForm):
    """Form to edit Policy to PolicyBindingModel Binding"""

    target = GroupedModelChoiceField(
        queryset=PolicyBindingModel.objects.all().select_subclasses(),
        to_field_name="pbm_uuid",
    )
    policy = GroupedModelChoiceField(
        queryset=Policy.objects.all().select_subclasses(), required=False
    )

    def __init__(self, *args, **kwargs):  # pragma: no cover
        super().__init__(*args, **kwargs)
        if "target" in self.initial:
            self.fields["target"].widget = forms.HiddenInput()

    class Meta:

        model = PolicyBinding
        fields = ["enabled", "policy", "group", "user", "target", "order", "timeout"]


class PolicyForm(forms.ModelForm):
    """Base Policy form"""

    class Meta:

        model = Policy
        fields = ["name", "execution_logging"]
