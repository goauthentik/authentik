"""passbook flows identification forms"""
from django import forms
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _
from structlog import get_logger

from passbook.lib.config import CONFIG
from passbook.lib.utils.ui import human_list
from passbook.stages.identification.models import IdentificationStage

LOGGER = get_logger()


class IdentificationStageForm(forms.ModelForm):
    """Form to create/edit IdentificationStage instances"""

    class Meta:

        model = IdentificationStage
        fields = ["name", "user_fields", "template"]
        widgets = {
            "name": forms.TextInput(),
        }


class IdentificationForm(forms.Form):
    """Allow users to login"""

    title = _("Log in to your account")
    uid_field = forms.CharField(label=_(""))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO: Get UID Fields from stage config
        if CONFIG.y("passbook.uid_fields") == ["e-mail"]:
            self.fields["uid_field"] = forms.EmailField()
        self.fields["uid_field"].label = human_list(
            [x.title() for x in CONFIG.y("passbook.uid_fields")]
        )

    def clean_uid_field(self):
        """Validate uid_field after EmailValidator if 'email' is the only selected uid_fields"""
        if CONFIG.y("passbook.uid_fields") == ["email"]:
            validate_email(self.cleaned_data.get("uid_field"))
        return self.cleaned_data.get("uid_field")
