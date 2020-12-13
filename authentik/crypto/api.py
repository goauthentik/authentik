"""Crypto API Views"""
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.x509 import load_pem_x509_certificate
from rest_framework.serializers import ModelSerializer, ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.crypto.models import CertificateKeyPair


class CertificateKeyPairSerializer(ModelSerializer):
    """CertificateKeyPair Serializer"""

    def validate_certificate_data(self, value):
        """Verify that input is a valid PEM x509 Certificate"""
        try:
            load_pem_x509_certificate(value.encode("utf-8"), default_backend())
        except ValueError:
            raise ValidationError("Unable to load certificate.")
        return value

    def validate_key_data(self, value):
        """Verify that input is a valid PEM RSA Key"""
        # Since this field is optional, data can be empty.
        if value != "":
            try:
                load_pem_private_key(
                    str.encode("\n".join([x.strip() for x in value.split("\n")])),
                    password=None,
                    backend=default_backend(),
                )
            except ValueError:
                raise ValidationError("Unable to load private key.")
        return value

    class Meta:

        model = CertificateKeyPair
        fields = ["pk", "name", "certificate_data", "key_data"]


class CertificateKeyPairViewSet(ModelViewSet):
    """CertificateKeyPair Viewset"""

    queryset = CertificateKeyPair.objects.all()
    serializer_class = CertificateKeyPairSerializer
