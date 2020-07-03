"""Flow and Stage forms"""

from django import forms
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
        ]
        help_texts = {
            "name": _("Shown as the Title in Flow pages."),
            "slug": _("Visible in the URL."),
            "designation": _(
                (
                    "Decides what this Flow is used for. For example, the Authentication flow "
                    "is redirect to when an un-authenticated user visits passbook."
                )
            ),
        }
        widgets = {
            "name": forms.TextInput(),
        }


class FlowStageBindingForm(forms.ModelForm):
    """FlowStageBinding Form"""

    class Meta:

        model = FlowStageBinding
        fields = [
            "target",
            "stage",
            "re_evaluate_policies",
            "order",
        ]
        labels = {
            "re_evaluate_policies": _("Re-evaluate Policies"),
        }
        widgets = {
            "name": forms.TextInput(),
        }
