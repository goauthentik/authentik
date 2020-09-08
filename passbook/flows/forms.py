"""Flow and Stage forms"""

from django import forms
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _

from passbook.flows.models import Flow, FlowStageBinding, Stage
from passbook.flows.transfer.importer import FlowImporter
from passbook.lib.widgets import GroupedModelChoiceField


class FlowForm(forms.ModelForm):
    """Flow Form"""

    class Meta:

        model = Flow
        fields = [
            "name",
            "title",
            "slug",
            "designation",
        ]
        help_texts = {
            "title": _("Shown as the Title in Flow pages."),
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
            "title": forms.TextInput(),
        }


class FlowStageBindingForm(forms.ModelForm):
    """FlowStageBinding Form"""

    stage = GroupedModelChoiceField(queryset=Stage.objects.all().select_subclasses())

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


class FlowImportForm(forms.Form):
    """Form used for flow importing"""

    flow = forms.FileField()

    def clean_flow(self):
        """Check if the flow is valid and rewind the file to the start"""
        flow = self.cleaned_data["flow"].read()
        valid = FlowImporter(flow.decode()).validate()
        if not valid:
            raise ValidationError(_("Flow invalid."))
        self.cleaned_data["flow"].seek(0)
        return self.cleaned_data["flow"]
