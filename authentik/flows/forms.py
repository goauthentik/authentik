"""Flow and Stage forms"""
from django import forms

from authentik.flows.models import FlowStageBinding, Stage
from authentik.lib.widgets import GroupedModelChoiceField


class FlowStageBindingForm(forms.ModelForm):
    """FlowStageBinding Form"""

    stage = GroupedModelChoiceField(
        queryset=Stage.objects.all().order_by("name").select_subclasses(),
        to_field_name="stage_uuid",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "target" in self.initial:
            self.fields["target"].widget = forms.HiddenInput()

    class Meta:

        model = FlowStageBinding
        fields = [
            "target",
            "stage",
            "evaluate_on_plan",
            "re_evaluate_policies",
            "order",
        ]
        widgets = {
            "name": forms.TextInput(),
        }
