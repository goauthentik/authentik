"""passbook administration forms"""
from django import forms

from passbook.admin.fields import CodeMirrorWidget, YAMLField
from passbook.core.models import User


class PolicyTestForm(forms.Form):
    """Form to test policies against user"""

    user = forms.ModelChoiceField(queryset=User.objects.all())
    context = YAMLField(widget=CodeMirrorWidget(), required=False, initial=dict)
