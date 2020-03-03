"""passbook Flow forms"""

from django import forms

from passbook.flows.models import Flow


class FlowForm(forms.ModelForm):
    """Flow Form"""

    class Meta:

        model = Flow
        fields = [
            "slug",
            "designation",
        ]
        widgets = {
            "slug": forms.TextInput(),
        }
