"""passbook core user forms"""

from django import forms
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _

from passbook.core.models import User


class UserDetailForm(forms.ModelForm):
    """Update User Details"""

    class Meta:

        model = User
        fields = ['username', 'name', 'email']
        widgets = {
            'name': forms.TextInput
        }

class PasswordChangeForm(forms.Form):
    """Form to update password"""

    password = forms.CharField(label=_('Password'),
                               widget=forms.PasswordInput(attrs={
                                   'placeholder': _('New Password'),
                                   'autocomplete': 'new-password'
                                   }))
    password_repeat = forms.CharField(label=_('Repeat Password'),
                                      widget=forms.PasswordInput(attrs={
                                          'placeholder': _('Repeat Password'),
                                          'autocomplete': 'new-password'
                                      }))

    def clean_password_repeat(self):
        """Check if Password adheres to filter and if passwords matche"""
        password = self.cleaned_data.get('password')
        password_repeat = self.cleaned_data.get('password_repeat')
        if password != password_repeat:
            raise ValidationError(_("Passwords don't match"))
        return self.cleaned_data.get('password_repeat')
