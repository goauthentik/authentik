"""passbook administrative user forms"""

from django import forms

from passbook.core.models import User


class UserForm(forms.ModelForm):
    """Update User Details"""

    class Meta:

        model = User
        fields = ['username', 'name', 'email', 'is_staff', 'is_active', 'attributes']
        widgets = {
            'name': forms.TextInput
        }
