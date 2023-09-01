"""Crypto tests"""
import datetime
from json import loads
from os import makedirs
from tempfile import TemporaryDirectory

from cryptography.x509.extensions import SubjectAlternativeName
from cryptography.x509.general_name import DNSName
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.api.used_by import DeleteAction
from authentik.core.tests.utils import create_test_admin_user, create_test_cert, create_test_flow
from authentik.crypto.api import CertificateKeyPairSerializer
from authentik.crypto.builder import CertificateBuilder
from authentik.crypto.models import CertificateKeyPair
from authentik.crypto.tasks import MANAGED_DISCOVERED, certificate_discovery
from authentik.lib.config import CONFIG
from authentik.lib.generators import generate_id, generate_key
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
                instance=keypair,
                data={
                    "name": keypair.name,
                    "certificate_data": keypair.certificate_data,
                    "key_data": keypair.key_data,
                },
            ).is_valid()
        )
        self.assertFalse(
            CertificateKeyPairSerializer(
                instance=keypair,
                data={
                    "name": keypair.name,
                    "certificate_data": "test",
                    "key_data": "test",
                },
            ).is_valid()
        )

    def test_builder(self):
        """Test Builder"""
        name = generate_id()
        builder = CertificateBuilder(name)
        with self.assertRaises(ValueError):
            builder.save()
        builder.build(
            subject_alt_names=[],
            validity_days=3,
        )
        instance = builder.save()
        now = datetime.datetime.today()
        self.assertEqual(instance.name, name)
        self.assertEqual((instance.certificate.not_valid_after - now).days, 2)

    def test_builder_api(self):
        """Test Builder (via API)"""
        self.client.force_login(create_test_admin_user())
        name = generate_id()
        self.client.post(
            reverse("authentik_api:certificatekeypair-generate"),
            data={"common_name": name, "subject_alt_name": "bar,baz", "validity_days": 3},
        )
        key = CertificateKeyPair.objects.filter(name=name).first()
        self.assertIsNotNone(key)
        ext: SubjectAlternativeName = key.certificate.extensions[0].value
        self.assertIsInstance(ext, SubjectAlternativeName)
        self.assertIsInstance(ext[0], DNSName)
        self.assertEqual(ext[0].value, "bar")
        self.assertIsInstance(ext[1], DNSName)
        self.assertEqual(ext[1].value, "baz")

    def test_builder_api_empty_san(self):
        """Test Builder (via API)"""
        self.client.force_login(create_test_admin_user())
        name = generate_id()
        self.client.post(
            reverse("authentik_api:certificatekeypair-generate"),
            data={"common_name": name, "subject_alt_name": "", "validity_days": 3},
        )
        key = CertificateKeyPair.objects.filter(name=name).first()
        self.assertIsNotNone(key)
        self.assertEqual(len(key.certificate.extensions), 0)

    def test_builder_api_empty_san_multiple(self):
        """Test Builder (via API)"""
        self.client.force_login(create_test_admin_user())
        name = generate_id()
        self.client.post(
            reverse("authentik_api:certificatekeypair-generate"),
            data={"common_name": name, "subject_alt_name": ", ", "validity_days": 3},
        )
        key = CertificateKeyPair.objects.filter(name=name).first()
        self.assertIsNotNone(key)
        self.assertEqual(len(key.certificate.extensions), 0)

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
        cert = create_test_cert()
        self.client.force_login(create_test_admin_user())
        response = self.client.get(
            reverse(
                "authentik_api:certificatekeypair-list",
            ),
            data={"name": cert.name},
        )
        self.assertEqual(200, response.status_code)
        body = loads(response.content.decode())
        api_cert = [x for x in body["results"] if x["name"] == cert.name][0]
        self.assertEqual(api_cert["fingerprint_sha1"], cert.fingerprint_sha1)
        self.assertEqual(api_cert["fingerprint_sha256"], cert.fingerprint_sha256)

    def test_list_has_key_false(self):
        """Test API List with has_key set to false"""
        cert = create_test_cert()
        cert.key_data = ""
        cert.save()
        self.client.force_login(create_test_admin_user())
        response = self.client.get(
            reverse(
                "authentik_api:certificatekeypair-list",
            ),
            data={"name": cert.name, "has_key": False},
        )
        self.assertEqual(200, response.status_code)
        body = loads(response.content.decode())
        api_cert = [x for x in body["results"] if x["name"] == cert.name][0]
        self.assertEqual(api_cert["fingerprint_sha1"], cert.fingerprint_sha1)
        self.assertEqual(api_cert["fingerprint_sha256"], cert.fingerprint_sha256)

    def test_list_without_details(self):
        """Test API List (no details)"""
        cert = create_test_cert()
        self.client.force_login(create_test_admin_user())
        response = self.client.get(
            reverse(
                "authentik_api:certificatekeypair-list",
            ),
            data={"name": cert.name, "include_details": False},
        )
        self.assertEqual(200, response.status_code)
        body = loads(response.content.decode())
        api_cert = [x for x in body["results"] if x["name"] == cert.name][0]
        self.assertEqual(api_cert["fingerprint_sha1"], None)
        self.assertEqual(api_cert["fingerprint_sha256"], None)

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
            ),
            data={"download": True},
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
            ),
            data={"download": True},
        )
        self.assertEqual(200, response.status_code)
        self.assertIn("Content-Disposition", response)

    def test_used_by(self):
        """Test used_by endpoint"""
        self.client.force_login(create_test_admin_user())
        keypair = create_test_cert()
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            client_secret=generate_key(),
            authorization_flow=create_test_flow(),
            redirect_uris="http://localhost",
            signing_key=keypair,
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

    def test_discovery(self):
        """Test certificate discovery"""
        name = generate_id()
        builder = CertificateBuilder(name)
        with self.assertRaises(ValueError):
            builder.save()
        builder.build(
            subject_alt_names=[],
            validity_days=3,
        )
        with TemporaryDirectory() as temp_dir:
            with open(f"{temp_dir}/foo.pem", "w+", encoding="utf-8") as _cert:
                _cert.write(builder.certificate)
            with open(f"{temp_dir}/foo.key", "w+", encoding="utf-8") as _key:
                _key.write(builder.private_key)
            makedirs(f"{temp_dir}/foo.bar", exist_ok=True)
            with open(f"{temp_dir}/foo.bar/fullchain.pem", "w+", encoding="utf-8") as _cert:
                _cert.write(builder.certificate)
            with open(f"{temp_dir}/foo.bar/privkey.pem", "w+", encoding="utf-8") as _key:
                _key.write(builder.private_key)
            with CONFIG.patch("cert_discovery_dir", temp_dir):
                certificate_discovery()  # pylint: disable=no-value-for-parameter
        keypair: CertificateKeyPair = CertificateKeyPair.objects.filter(
            managed=MANAGED_DISCOVERED % "foo"
        ).first()
        self.assertIsNotNone(keypair)
        self.assertIsNotNone(keypair.certificate)
        self.assertIsNotNone(keypair.private_key)
        self.assertTrue(
            CertificateKeyPair.objects.filter(managed=MANAGED_DISCOVERED % "foo.bar").exists()
        )
