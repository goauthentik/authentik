"""authentik Event Matcher Policy forms"""

from django import forms
from django.utils.translation import gettext_lazy as _

from authentik.policies.event_matcher.models import EventMatcherPolicy
from authentik.policies.forms import PolicyForm


class EventMatcherPolicyForm(PolicyForm):
    """EventMatcherPolicy Form"""

    class Meta:

        model = EventMatcherPolicy
        fields = PolicyForm.Meta.fields + [
            "action",
            "client_ip",
            "app",
        ]
        widgets = {
            "name": forms.TextInput(),
            "client_ip": forms.TextInput(),
        }
        labels = {"client_ip": _("Client IP")}
