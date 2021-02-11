"""authentik Policy forms"""

from django import forms
from django.utils.translation import gettext as _

from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.forms import PolicyForm


class DummyPolicyForm(PolicyForm):
    """DummyPolicyForm Form"""

    class Meta:

        model = DummyPolicy
        fields = PolicyForm.Meta.fields + ["result", "wait_min", "wait_max"]
        widgets = {
            "name": forms.TextInput(),
        }
        labels = {"result": _("Allow user")}
