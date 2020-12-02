"""authentik Core Group forms"""
from django import forms

from authentik.admin.fields import CodeMirrorWidget, YAMLField
from authentik.core.models import Group, User


class GroupForm(forms.ModelForm):
    """Group Form"""

    members = forms.ModelMultipleChoiceField(
        User.objects.all(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial["members"] = self.instance.users.values_list("pk", flat=True)

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)
        if instance.pk:
            instance.users.clear()
            instance.users.add(*self.cleaned_data["members"])
        return instance

    class Meta:

        model = Group
        fields = ["name", "is_superuser", "parent", "members", "attributes"]
        widgets = {
            "name": forms.TextInput(),
            "attributes": CodeMirrorWidget,
        }
        field_classes = {
            "attributes": YAMLField,
        }
