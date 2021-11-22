"""Crypto tests"""
import datetime

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.api.used_by import DeleteAction
from authentik.core.tests.utils import create_test_admin_user, create_test_cert, create_test_flow
from authentik.crypto.api import CertificateKeyPairSerializer
from authentik.crypto.builder import CertificateBuilder
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.generators import generate_key
from authentik.providers.oauth2.models import OAuth2Provider


class TestCrypto(APITestCase):
    """Test Crypto validation"""

    def test_model_private(self):
        """Test model private key"""
        cert = CertificateKeyPair.objects.create(
            name="test",
            certificate_data="foo",
            key_data="foo",
        )
        self.assertIsNone(cert.private_key)

    def test_serializer(self):
        """Test API Validation"""
        keypair = create_test_cert()
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

    def test_builder_api(self):
        """Test Builder (via API)"""
        self.client.force_login(create_test_admin_user())
        self.client.post(
            reverse("authentik_api:certificatekeypair-generate"),
            data={"common_name": "foo", "subject_alt_name": "bar,baz", "validity_days": 3},
        )
        self.assertTrue(CertificateKeyPair.objects.filter(name="foo").exists())

    def test_builder_api_invalid(self):
        """Test Builder (via API) (invalid)"""
        self.client.force_login(create_test_admin_user())
        response = self.client.post(
            reverse("authentik_api:certificatekeypair-generate"),
            data={},
        )
        self.assertEqual(response.status_code, 400)

    def test_list(self):
        """Test API List"""
        self.client.force_login(create_test_admin_user())
        response = self.client.get(
            reverse(
                "authentik_api:certificatekeypair-list",
            )
        )
        self.assertEqual(200, response.status_code)

    def test_certificate_download(self):
        """Test certificate export (download)"""
        self.client.force_login(create_test_admin_user())
        keypair = create_test_cert()
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
        self.client.force_login(create_test_admin_user())
        keypair = create_test_cert()
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

    def test_used_by(self):
        """Test used_by endpoint"""
        self.client.force_login(create_test_admin_user())
        keypair = create_test_cert()
        provider = OAuth2Provider.objects.create(
            name="test",
            client_id="test",
            client_secret=generate_key(),
            authorization_flow=create_test_flow(),
            redirect_uris="http://localhost",
            rsa_key=keypair,
        )
        response = self.client.get(
            reverse(
                "authentik_api:certificatekeypair-used-by",
                kwargs={"pk": keypair.pk},
            )
        )
        self.assertEqual(200, response.status_code)
        self.assertJSONEqual(
            response.content.decode(),
            [
                {
                    "app": "authentik_providers_oauth2",
                    "model_name": "oauth2provider",
                    "pk": str(provider.pk),
                    "name": str(provider),
                    "action": DeleteAction.SET_NULL.name,
                }
            ],
        )
