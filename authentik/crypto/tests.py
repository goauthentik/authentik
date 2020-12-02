"""Crypto tests"""
from django.test import TestCase

from authentik.crypto.api import CertificateKeyPairSerializer
from authentik.crypto.forms import CertificateKeyPairForm
from authentik.crypto.models import CertificateKeyPair


class TestCrypto(TestCase):
    """Test Crypto validation"""

    def test_form(self):
        """Test form validation"""
        keypair = CertificateKeyPair.objects.first()
        self.assertTrue(
            CertificateKeyPairForm(
                {
                    "name": keypair.name,
                    "certificate_data": keypair.certificate_data,
                    "key_data": keypair.key_data,
                }
            ).is_valid()
        )
        self.assertFalse(
            CertificateKeyPairForm(
                {"name": keypair.name, "certificate_data": "test", "key_data": "test"}
            ).is_valid()
        )

    def test_serializer(self):
        """Test API Validation"""
        keypair = CertificateKeyPair.objects.first()
        self.assertTrue(
            CertificateKeyPairSerializer(
                data={
                    "name": keypair.name,
                    "certificate_data": keypair.certificate_data,
                    "key_data": keypair.key_data,
                }
            ).is_valid()
        )
        self.assertFalse(
            CertificateKeyPairSerializer(
                data={
                    "name": keypair.name,
                    "certificate_data": "test",
                    "key_data": "test",
                }
            ).is_valid()
        )
