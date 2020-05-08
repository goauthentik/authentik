"""factor forms"""

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _

from passbook.flows.models import Flow, FlowFactorBinding

GENERAL_FIELDS = ["name", "slug", "order", "policies", "enabled"]


class FlowForm(forms.ModelForm):
    """Flow Form"""

    class Meta:

        model = Flow
        fields = [
            "name",
            "slug",
            "designation",
            "factors",
            "policies",
        ]
        widgets = {
            "name": forms.TextInput(),
            "factors": FilteredSelectMultiple(_("policies"), False),
        }


class FlowFactorBindingForm(forms.ModelForm):
    """FlowFactorBinding Form"""

    class Meta:

        model = FlowFactorBinding
        fields = [
            "flow",
            "factor",
            "re_evaluate_policies",
            "order",
            "policies",
        ]
        widgets = {
            "name": forms.TextInput(),
            "factors": FilteredSelectMultiple(_("policies"), False),
        }
