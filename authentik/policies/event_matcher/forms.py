"""authentik Event Matcher Policy forms"""

from django import forms
from django.utils.translation import gettext_lazy as _

from authentik.policies.event_matcher.models import EventMatcherPolicy
from authentik.policies.forms import GENERAL_FIELDS


class EventMatcherPolicyForm(forms.ModelForm):
    """EventMatcherPolicy Form"""

    class Meta:

        model = EventMatcherPolicy
        fields = GENERAL_FIELDS + [
            "action",
            "client_ip",
            "app",
        ]
        widgets = {
            "name": forms.TextInput(),
            "client_ip": forms.TextInput(),
        }
        labels = {"client_ip": _("Client IP")}
