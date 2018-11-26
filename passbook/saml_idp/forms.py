"""passbook SAML IDP Forms"""

from django import forms

from passbook.saml_idp.models import SAMLProvider


class SAMLProviderForm(forms.ModelForm):
    """SAML Provider form"""

    class Meta:

        model = SAMLProvider
        fields = ['name', 'acs_url', 'processor_path', ]
