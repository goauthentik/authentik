"""passbook Application Security Gateway Forms"""

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.forms import ValidationError
from django.utils.translation import gettext as _

from passbook.app_gw.models import ApplicationGatewayProvider, RewriteRule
from passbook.lib.fields import DynamicArrayField


class ApplicationGatewayProviderForm(forms.ModelForm):
    """Security Gateway Provider form"""

    def clean_server_name(self):
        """Check if server_name is in DB already, since
        Postgres ArrayField doesn't suppport keys."""
        current = self.cleaned_data.get('server_name')
        if ApplicationGatewayProvider.objects \
                .filter(server_name__overlap=current) \
                .exclude(pk=self.instance.pk).exists():
            raise ValidationError("Server Name already in use.")
        return current

    class Meta:

        model = ApplicationGatewayProvider
        fields = ['server_name', 'upstream', 'enabled', 'authentication_header',
                  'default_content_type', 'upstream_ssl_verification', 'property_mappings']
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
            'upstream_ssl_verification': _('Verify upstream SSL Certificates?'),
            'property_mappings': _('Rewrite Rules')
        }

class RewriteRuleForm(forms.ModelForm):
    """Rewrite Rule Form"""

    class Meta:

        model = RewriteRule
        fields = ['name', 'match', 'halt', 'replacement', 'redirect', 'conditions']
        widgets = {
            'name': forms.TextInput(),
            'match': forms.TextInput(attrs={'data-is-monospace': True}),
            'replacement': forms.TextInput(attrs={'data-is-monospace': True}),
            'conditions': FilteredSelectMultiple(_('Conditions'), False)
        }
