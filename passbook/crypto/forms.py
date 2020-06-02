"""passbook Crypto forms"""
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.x509 import load_pem_x509_certificate
from django import forms
from django.utils.translation import gettext_lazy as _

from passbook.crypto.models import CertificateKeyPair


class CertificateKeyPairForm(forms.ModelForm):
    """CertificateKeyPair Form"""

    def clean_certificate_data(self):
        """Verify that input is a valid PEM x509 Certificate"""
        certificate_data = self.cleaned_data["certificate_data"]
        try:
            load_pem_x509_certificate(
                certificate_data.encode("utf-8"), default_backend()
            )
        except ValueError:
            raise forms.ValidationError("Unable to load certificate.")
        return certificate_data

    def clean_key_data(self):
        """Verify that input is a valid PEM RSA Key"""
        key_data = self.cleaned_data["key_data"]
        # Since this field is optional, data can be empty.
        if key_data == "":
            return key_data
        try:
            load_pem_private_key(
                str.encode("\n".join([x.strip() for x in key_data.split("\n")])),
                password=None,
                backend=default_backend(),
            )
        except ValueError:
            raise forms.ValidationError("Unable to load private key.")
        return key_data

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
