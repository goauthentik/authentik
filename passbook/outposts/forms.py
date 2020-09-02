"""Outpost forms"""

from django import forms
from django.utils.translation import gettext_lazy as _

from passbook.admin.fields import CodeMirrorWidget, YAMLField
from passbook.core.models import Provider
from passbook.outposts.models import Outpost


class OutpostForm(forms.ModelForm):
    """Outpost Form"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["providers"].queryset = Provider.objects.all().select_subclasses()

    class Meta:

        model = Outpost
        fields = [
            "name",
            "type",
            "deployment_type",
            "providers",
            "config",
        ]
        widgets = {
            "name": forms.TextInput(),
            "config": CodeMirrorWidget,
        }
        field_classes = {
            "config": YAMLField,
        }
        labels = {"config": _("Configuration")}
