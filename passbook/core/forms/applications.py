"""passbook Core Application forms"""
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _

from passbook.core.models import Application, Provider


class ApplicationForm(forms.ModelForm):
    """Application Form"""

    provider = forms.ModelChoiceField(
        queryset=Provider.objects.all().order_by('pk').select_subclasses(), required=False
    )

    class Meta:

        model = Application
        fields = [
            "name",
            "slug",
            "skip_authorization",
            "provider",
            "meta_launch_url",
            "meta_icon_url",
            "meta_description",
            "meta_publisher",
            "policies",
        ]
        widgets = {
            "name": forms.TextInput(),
            "meta_launch_url": forms.TextInput(),
            "meta_icon_url": forms.TextInput(),
            "meta_publisher": forms.TextInput(),
            "policies": FilteredSelectMultiple(_("policies"), False),
        }
        labels = {
            "meta_launch_url": _("Launch URL"),
            "meta_icon_url": _("Icon URL"),
            "meta_description": _("Description"),
            "meta_publisher": _("Publisher"),
        }
        help_texts = {"policies": _("Policies required to access this Application.")}
