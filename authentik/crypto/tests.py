"""Crypto tests"""
import datetime

from django.test import TestCase
from django.urls import reverse

from authentik.core.models import User
from authentik.crypto.api import CertificateKeyPairSerializer
from authentik.crypto.builder import CertificateBuilder
from authentik.crypto.models import CertificateKeyPair


class TestCrypto(TestCase):
    """Test Crypto validation"""

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

    def test_builder(self):
        """Test Builder"""
        builder = CertificateBuilder()
        builder.common_name = "test-cert"
        with self.assertRaises(ValueError):
            builder.save()
        builder.build(
            subject_alt_names=[],
            validity_days=3,
        )
        instance = builder.save()
        now = datetime.datetime.today()
        self.assertEqual(instance.name, "test-cert")
        self.assertEqual((instance.certificate.not_valid_after - now).days, 2)

    def test_certificate_download(self):
        """Test certificate export (download)"""
        self.client.force_login(User.objects.get(username="akadmin"))
        keypair = CertificateKeyPair.objects.first()
        response = self.client.get(
            reverse(
                "authentik_api:certificatekeypair-view-certificate",
                kwargs={"pk": keypair.pk},
            )
        )
        self.assertEqual(200, response.status_code)
        response = self.client.get(
            reverse(
                "authentik_api:certificatekeypair-view-certificate",
                kwargs={"pk": keypair.pk},
            )
            + "?download",
        )
        self.assertEqual(200, response.status_code)
        self.assertIn("Content-Disposition", response)

    def test_private_key_download(self):
        """Test private_key export (download)"""
        self.client.force_login(User.objects.get(username="akadmin"))
        keypair = CertificateKeyPair.objects.first()
        response = self.client.get(
            reverse(
                "authentik_api:certificatekeypair-view-private-key",
                kwargs={"pk": keypair.pk},
            )
        )
        self.assertEqual(200, response.status_code)
        response = self.client.get(
            reverse(
                "authentik_api:certificatekeypair-view-private-key",
                kwargs={"pk": keypair.pk},
            )
            + "?download",
        )
        self.assertEqual(200, response.status_code)
        self.assertIn("Content-Disposition", response)
