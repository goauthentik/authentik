"""Outpost forms"""

from django import forms

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
            "providers",
        ]
        widgets = {
            "name": forms.TextInput(),
        }
