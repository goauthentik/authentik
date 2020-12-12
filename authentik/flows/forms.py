"""Flow and Stage forms"""

from django import forms
from django.core.validators import FileExtensionValidator
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _

from authentik.flows.models import Flow, FlowStageBinding, Stage
from authentik.flows.transfer.importer import FlowImporter
from authentik.lib.widgets import GroupedModelChoiceField


class FlowForm(forms.ModelForm):
    """Flow Form"""

    class Meta:

        model = Flow
        fields = [
            "name",
            "title",
            "slug",
            "designation",
            "background",
        ]
        widgets = {
            "name": forms.TextInput(),
            "title": forms.TextInput(),
            "background": forms.FileInput(),
        }


class FlowStageBindingForm(forms.ModelForm):
    """FlowStageBinding Form"""

    stage = GroupedModelChoiceField(
        queryset=Stage.objects.all().select_subclasses(), to_field_name="stage_uuid"
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


class FlowImportForm(forms.Form):
    """Form used for flow importing"""

    flow = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=["akflow"])]
    )

    def clean_flow(self):
        """Check if the flow is valid and rewind the file to the start"""
        flow = self.cleaned_data["flow"].read()
        valid = FlowImporter(flow.decode()).validate()
        if not valid:
            raise ValidationError(_("Flow invalid."))
        self.cleaned_data["flow"].seek(0)
        return self.cleaned_data["flow"]
