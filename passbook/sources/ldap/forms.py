"""passbook LDAP Forms"""

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _

from passbook.admin.forms.source import SOURCE_FORM_FIELDS
from passbook.sources.ldap.models import LDAPSource


class LDAPSourceForm(forms.ModelForm):
    """LDAPSource Form"""

    class Meta:

        model = LDAPSource
        fields = SOURCE_FORM_FIELDS + [
            'server_uri',
            'bind_cn',
            'bind_password',
            'start_tls',
            'base_dn',
            'additional_user_dn',
            'additional_group_dn',
            'user_object_filter',
            'group_object_filter',
            'sync_groups',
            'sync_parent_group',
        ]
        widgets = {
            'name': forms.TextInput(),
            'server_uri': forms.TextInput(),
            'bind_cn': forms.TextInput(),
            'bind_password': forms.PasswordInput(),
            'base_dn': forms.TextInput(),
            'additional_user_dn': forms.TextInput(),
            'additional_group_dn': forms.TextInput(),
            'user_object_filter': forms.TextInput(),
            'group_object_filter': forms.TextInput(),
            'policies': FilteredSelectMultiple(_('policies'), False)
        }
        labels = {
            'server_uri': _('Server URI'),
            'bind_cn': _('Bind CN'),
            'start_tls': _('Enable Start TLS'),
            'base_dn': _('Base DN'),
            'additional_user_dn': _('Addition User DN'),
            'additional_group_dn': _('Addition Group DN'),
        }
