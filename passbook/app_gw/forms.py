"""passbook Application Security Gateway Forms"""

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext as _

from passbook.app_gw.models import ApplicationGatewayProvider
from passbook.lib.fields import DynamicArrayField


class ApplicationGatewayProviderForm(forms.ModelForm):
    """Security Gateway Provider form"""

    class Meta:

        model = ApplicationGatewayProvider
        fields = ['server_name', 'upstream', 'enabled', 'authentication_header',
                  'default_content_type', 'upstream_ssl_verification']
        widgets = {
            'authentication_header': forms.TextInput(),
            'default_content_type': forms.TextInput(),
            'property_mappings': FilteredSelectMultiple(_('Property Mappings'), False)
        }
        field_classes = {
            'server_name': DynamicArrayField,
            'upstream': DynamicArrayField
        }
        labels = {
            'upstream_ssl_verification': _('Verify upstream SSL Certificates?')
        }
