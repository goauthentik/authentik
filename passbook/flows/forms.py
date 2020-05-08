"""Flow and Stage forms"""

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _

from passbook.flows.models import Flow, FlowStageBinding


class FlowForm(forms.ModelForm):
    """Flow Form"""

    class Meta:

        model = Flow
        fields = [
            "name",
            "slug",
            "designation",
            "stages",
            "policies",
        ]
        widgets = {
            "name": forms.TextInput(),
            "stages": FilteredSelectMultiple(_("stages"), False),
            "policies": FilteredSelectMultiple(_("policies"), False),
        }


class FlowStageBindingForm(forms.ModelForm):
    """FlowStageBinding Form"""

    class Meta:

        model = FlowStageBinding
        fields = [
            "flow",
            "stage",
            "re_evaluate_policies",
            "order",
            "policies",
        ]
        widgets = {
            "name": forms.TextInput(),
            "policies": FilteredSelectMultiple(_("policies"), False),
        }
