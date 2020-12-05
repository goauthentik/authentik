"""authentik administrative user forms"""

from django import forms

from authentik.admin.fields import CodeMirrorWidget, YAMLField
from authentik.core.models import User


class UserForm(forms.ModelForm):
    """Update User Details"""

    class Meta:

        model = User
        fields = ["username", "name", "email", "is_active", "attributes"]
        widgets = {
            "name": forms.TextInput,
            "attributes": CodeMirrorWidget,
        }
        field_classes = {
            "attributes": YAMLField,
        }
