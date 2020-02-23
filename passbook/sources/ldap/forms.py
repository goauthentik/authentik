"""passbook LDAP Forms"""

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _

from passbook.admin.forms.source import SOURCE_FORM_FIELDS
from passbook.sources.ldap.models import LDAPPropertyMapping, LDAPSource


class LDAPSourceForm(forms.ModelForm):
    """LDAPSource Form"""

    class Meta:

        model = LDAPSource
        fields = SOURCE_FORM_FIELDS + [
            "server_uri",
            "bind_cn",
            "bind_password",
            "start_tls",
            "base_dn",
            "additional_user_dn",
            "additional_group_dn",
            "user_object_filter",
            "group_object_filter",
            "user_group_membership_field",
            "object_uniqueness_field",
            "sync_groups",
            "sync_parent_group",
            "property_mappings",
        ]
        widgets = {
            "name": forms.TextInput(),
            "server_uri": forms.TextInput(),
            "bind_cn": forms.TextInput(),
            "bind_password": forms.TextInput(),
            "base_dn": forms.TextInput(),
            "additional_user_dn": forms.TextInput(),
            "additional_group_dn": forms.TextInput(),
            "user_object_filter": forms.TextInput(),
            "group_object_filter": forms.TextInput(),
            "user_group_membership_field": forms.TextInput(),
            "object_uniqueness_field": forms.TextInput(),
            "property_mappings": FilteredSelectMultiple(_("Property Mappings"), False),
        }


class LDAPPropertyMappingForm(forms.ModelForm):
    """LDAP Property Mapping form"""

    template_name = "ldap/property_mapping_form.html"

    class Meta:

        model = LDAPPropertyMapping
        fields = ["name", "object_field", "expression"]
        widgets = {
            "name": forms.TextInput(),
            "ldap_property": forms.TextInput(),
            "object_field": forms.TextInput(),
        }
