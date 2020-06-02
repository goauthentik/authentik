"""passbook flows identification forms"""
from django import forms
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _
from structlog import get_logger

from passbook.lib.utils.ui import human_list
from passbook.stages.identification.models import IdentificationStage, UserFields

LOGGER = get_logger()


class IdentificationStageForm(forms.ModelForm):
    """Form to create/edit IdentificationStage instances"""

    class Meta:

        model = IdentificationStage
        fields = ["name", "user_fields", "template", "enrollment_flow", "recovery_flow"]
        widgets = {
            "name": forms.TextInput(),
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
        self.fields["uid_field"].label = human_list(
            [x.title() for x in self.stage.user_fields]
        )

    def clean_uid_field(self):
        """Validate uid_field after EmailValidator if 'email' is the only selected uid_fields"""
        if self.stage.user_fields == [UserFields.E_MAIL]:
            validate_email(self.cleaned_data.get("uid_field"))
        return self.cleaned_data.get("uid_field")
