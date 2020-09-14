"""passbook Core Application forms"""
from django import forms
from django.utils.translation import gettext_lazy as _

from passbook.core.models import Application, Provider
from passbook.lib.widgets import GroupedModelChoiceField


class ApplicationForm(forms.ModelForm):
    """Application Form"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["provider"].queryset = (
            Provider.objects.all().order_by("pk").select_subclasses()
        )

    class Meta:

        model = Application
        fields = [
            "name",
            "slug",
            "provider",
            "meta_launch_url",
            "meta_icon_url",
            "meta_description",
            "meta_publisher",
        ]
        widgets = {
            "name": forms.TextInput(),
            "meta_launch_url": forms.TextInput(
                attrs={
                    "placeholder": _(
                        (
                            "If left empty, passbook will try to extract the launch URL "
                            "based on the selected provider."
                        )
                    )
                }
            ),
            "meta_icon_url": forms.TextInput(),
            "meta_publisher": forms.TextInput(),
        }
        field_classes = {"provider": GroupedModelChoiceField}
        labels = {
            "meta_launch_url": _("Launch URL"),
            "meta_icon_url": _("Icon URL"),
            "meta_description": _("Description"),
            "meta_publisher": _("Publisher"),
        }
