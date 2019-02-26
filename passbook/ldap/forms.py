"""passbook LDAP Forms"""

from django import forms
from django.utils.translation import gettext_lazy as _

from passbook.admin.forms.source import SOURCE_FORM_FIELDS
from passbook.ldap.models import LDAPSource


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
        }
        labels = {
            'server_uri': _('Server URI'),
            'bind_cn': _('Bind CN'),
            'base_dn': _('Base DN'),
        }

# class GeneralSettingsForm(SettingsForm):
#     """general settings form"""
#     MODE_AUTHENTICATION_BACKEND = 'auth_backend'
#     MODE_CREATE_USERS = 'create_users'
#     MODE_CHOICES = (
#         (MODE_AUTHENTICATION_BACKEND, _('Authentication Backend')),
#         (MODE_CREATE_USERS, _('Create Users'))
#     )

#     namespace = 'passbook.ldap'
#     settings = ['enabled', 'mode']

#     widgets = {
#         'enabled': forms.BooleanField(required=False),
#         'mode': forms.ChoiceField(widget=forms.RadioSelect, choices=MODE_CHOICES),
#     }


# class ConnectionSettings(SettingsForm):
#     """Connection settings form"""

#     namespace = 'passbook.ldap'
#     settings = ['server', 'server:tls', 'bind:user', 'bind:password', 'domain']

#     attrs_map = {
#         'server': {'placeholder': 'dc1.corp.exmaple.com'},
#         'bind:user': {'placeholder': 'Administrator'},
#         'domain': {'placeholder': 'corp.example.com'},
#     }

#     widgets = {
#         'server:tls': forms.BooleanField(required=False, label=_('Server TLS')),
#     }


# class AuthenticationBackendSettings(SettingsForm):
#     """Authentication backend settings"""

#     namespace = 'passbook.ldap'
#     settings = ['base']

#     attrs_map = {
#         'base': {'placeholder': 'DN in which to search for users'},
#     }


# class CreateUsersSettings(SettingsForm):
#     """Create users settings"""

#     namespace = 'passbook.ldap'
#     settings = ['create_base']

#     attrs_map = {
#         'create_base': {'placeholder': 'DN in which to create users'},
#     }
