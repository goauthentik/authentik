"""passbook Crypto forms"""
from django import forms
from django.utils.translation import gettext_lazy as _

from passbook.crypto.models import CertificateKeyPair


class CertificateKeyPairForm(forms.ModelForm):
    """CertificateKeyPair Form"""

    class Meta:

        model = CertificateKeyPair
        fields = [
            "name",
            "certificate_data",
            "key_data",
        ]
        widgets = {
            "name": forms.TextInput(),
            "certificate_data": forms.Textarea(attrs={"class": "monospaced"}),
            "key_data": forms.Textarea(attrs={"class": "monospaced"}),
        }
        labels = {
            "certificate_data": _("Certificate"),
            "key_data": _("Private Key"),
        }
