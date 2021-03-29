"""authentik events NotificationTransport forms"""
from django import forms

from authentik.events.models import NotificationRule


class NotificationRuleForm(forms.ModelForm):
    """NotificationRule Form"""

    class Meta:

        model = NotificationRule
        fields = [
            "name",
            "group",
            "transports",
            "severity",
        ]
        widgets = {
            "name": forms.TextInput(),
        }
