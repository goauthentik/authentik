"""passbook LDAP Forms"""

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _

from passbook.admin.forms.source import SOURCE_FORM_FIELDS
from passbook.core.forms.policies import GENERAL_FIELDS
from passbook.ldap.models import LDAPGroupMembershipPolicy, LDAPSource


class LDAPSourceForm(forms.ModelForm):
    """LDAPSource Form"""

    class Meta:

        model = LDAPSource
        fields = SOURCE_FORM_FIELDS + ['server_uri', 'bind_cn', 'bind_password',
                                       'type', 'domain', 'base_dn', 'create_user',
                                       'reset_password']
        widgets = {
            'name': forms.TextInput(),
            'server_uri': forms.TextInput(),
            'bind_cn': forms.TextInput(),
            'bind_password': forms.TextInput(),
            'domain': forms.TextInput(),
            'base_dn': forms.TextInput(),
            'policies': FilteredSelectMultiple(_('policies'), False)
        }
        labels = {
            'server_uri': _('Server URI'),
            'bind_cn': _('Bind CN'),
            'base_dn': _('Base DN'),
        }


class LDAPGroupMembershipPolicyForm(forms.ModelForm):
    """LDAPGroupMembershipPolicy Form"""

    class Meta:

        model = LDAPGroupMembershipPolicy
        fields = GENERAL_FIELDS + ['dn', ]
        widgets = {
            'name': forms.TextInput(),
            'dn': forms.TextInput(),
        }
        labels = {
            'dn': _('DN')
        }
