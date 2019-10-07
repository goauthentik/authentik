"""passbook administration forms"""
from django import forms
from django.conf import settings
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext as _

from passbook.factors.forms import GENERAL_FIELDS
from passbook.factors.password.models import PasswordFactor
from passbook.lib.utils.reflection import path_to_class


def get_authentication_backends():
    """Return all available authentication backends as tuple set"""
    for backend in settings.AUTHENTICATION_BACKENDS:
        klass = path_to_class(backend)
        yield backend, getattr(klass(), 'name', '%s (%s)' % (klass.__name__, klass.__module__))


class PasswordFactorForm(forms.ModelForm):
    """Form to create/edit Password Factors"""

    class Meta:

        model = PasswordFactor
        fields = GENERAL_FIELDS + ['backends', 'password_policies']
        widgets = {
            'name': forms.TextInput(),
            'order': forms.NumberInput(),
            'policies': FilteredSelectMultiple(_('policies'), False),
            'backends': FilteredSelectMultiple(_('backends'), False,
                                               choices=get_authentication_backends()),
            'password_policies': FilteredSelectMultiple(_('password policies'), False),
        }
