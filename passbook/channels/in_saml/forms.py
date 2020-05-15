"""passbook SAML SP Forms"""

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext as _

from passbook.admin.forms.inlet import INLET_FORM_FIELDS
from passbook.channels.in_saml.models import SAMLInlet


class SAMLInletForm(forms.ModelForm):
    """SAML Inlet form"""

    class Meta:

        model = SAMLInlet
        fields = INLET_FORM_FIELDS + [
            "issuer",
            "idp_url",
            "idp_logout_url",
            "auto_logout",
            "signing_kp",
        ]
        widgets = {
            "name": forms.TextInput(),
            "policies": FilteredSelectMultiple(_("policies"), False),
            "issuer": forms.TextInput(),
            "idp_url": forms.TextInput(),
            "idp_logout_url": forms.TextInput(),
        }
