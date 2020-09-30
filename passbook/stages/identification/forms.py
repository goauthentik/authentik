"""passbook flows identification forms"""
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _
from structlog import get_logger

from passbook.flows.models import Flow, FlowDesignation
from passbook.lib.utils.ui import human_list
from passbook.stages.identification.models import IdentificationStage, UserFields

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
            "template",
            "enrollment_flow",
            "recovery_flow",
        ]
        widgets = {
            "name": forms.TextInput(),
            "user_fields": FilteredSelectMultiple(
                _("fields"), False, choices=UserFields.choices
            ),
        }


class IdentificationForm(forms.Form):
    """Allow users to login"""

    stage: IdentificationStage

    title = _("Log in to your account")
    uid_field = forms.CharField(label=_(""))

    def __init__(self, *args, **kwargs):
        self.stage = kwargs.pop("stage")
        super().__init__(*args, **kwargs)
        if self.stage.user_fields == [UserFields.E_MAIL]:
            self.fields["uid_field"] = forms.EmailField()
        label = human_list([x.title() for x in self.stage.user_fields])
        self.fields["uid_field"].label = label
        self.fields["uid_field"].widget.attrs.update(
            {
                "placeholder": _(label),
                "autofocus": "autofocus",
                # Autocomplete according to
                # https://www.chromium.org/developers/design-documents/form-styles-that-chromium-understands
                "autocomplete": "username",
            }
        )

    def clean_uid_field(self):
        """Validate uid_field after EmailValidator if 'email' is the only selected uid_fields"""
        if self.stage.user_fields == [UserFields.E_MAIL]:
            validate_email(self.cleaned_data.get("uid_field"))
        return self.cleaned_data.get("uid_field")
