"""authentik flows identification forms"""
from django import forms
from structlog.stdlib import get_logger

from authentik.admin.fields import ArrayFieldSelectMultiple
from authentik.flows.models import Flow, FlowDesignation
from authentik.stages.identification.models import IdentificationStage, UserFields

LOGGER = get_logger()


class IdentificationStageForm(forms.ModelForm):
    """Form to create/edit IdentificationStage instances"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["enrollment_flow"].queryset = Flow.objects.filter(
            designation=FlowDesignation.ENROLLMENT
        )
        self.fields["recovery_flow"].queryset = Flow.objects.filter(
            designation=FlowDesignation.RECOVERY
        )

    class Meta:

        model = IdentificationStage
        fields = [
            "name",
            "user_fields",
            "case_insensitive_matching",
            "show_matched_user",
            "enrollment_flow",
            "recovery_flow",
        ]
        widgets = {
            "name": forms.TextInput(),
            "user_fields": ArrayFieldSelectMultiple(choices=UserFields.choices),
        }
