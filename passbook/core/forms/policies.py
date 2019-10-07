"""passbook Policy forms"""

from django import forms
from django.utils.translation import gettext as _

from passbook.core.models import DebugPolicy
from passbook.policies.forms import GENERAL_FIELDS


class DebugPolicyForm(forms.ModelForm):
    """DebugPolicyForm Form"""

    class Meta:

        model = DebugPolicy
        fields = GENERAL_FIELDS + ['result', 'wait_min', 'wait_max']
        widgets = {
            'name': forms.TextInput(),
        }
        labels = {
            'result': _('Allow user')
        }
