"""passbook Core Group forms"""
from django import forms

from passbook.core.models import Group, User
from django.contrib.admin.widgets import FilteredSelectMultiple


class GroupForm(forms.ModelForm):
    """Group Form"""

    members = forms.ModelMultipleChoiceField(
        User.objects.all(), required=False, widget=FilteredSelectMultiple('users', False))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial['members'] = self.instance.user_set.values_list('pk', flat=True)

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)
        if instance.pk:
            instance.user_set.clear()
            instance.user_set.add(*self.cleaned_data['members'])
        return instance

    class Meta:

        model = Group
        fields = ['name', 'parent', 'members', 'tags']
        widgets = {
            'name': forms.TextInput(),
        }
