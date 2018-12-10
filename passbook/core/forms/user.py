"""passbook core user forms"""

from django import forms

from passbook.core.models import User


class UserDetailForm(forms.ModelForm):
    """Update User Details"""

    class Meta:

        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
