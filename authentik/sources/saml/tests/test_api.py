"""SAML Source API tests"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_cert, create_test_flow
from authentik.crypto.builder import PrivateKeyAlg
from authentik.lib.generators import generate_id


class TestSAMLSourceAPI(APITestCase):
    """SAML Source API tests"""

    def setUp(self) -> None:
        super().setUp()
        self.client.force_login(create_test_admin_user())

    def test_create_validate_unsupported_key_type(self):
        """Test validation rejects key types without an XML-DSIG transform (Ed25519)"""
        ed25519_cert = create_test_cert(PrivateKeyAlg.ED25519)

        response = self.client.post(
            reverse("authentik_api:samlsource-list"),
            data={
                "name": generate_id(),
                "slug": generate_id(),
                "sso_url": "http://localhost",
                "pre_authentication_flow": create_test_flow().pk,
                "signing_kp": ed25519_cert.pk,
                "verification_kp": ed25519_cert.pk,
                "encryption_kp": ed25519_cert.pk,
                "signed_assertion": True,
            },
        )
        self.assertEqual(response.status_code, 400)
        message = (
            "Key type Ed25519 is not supported. Supported key types are: RSA, Elliptic Curve, DSA."
        )
        self.assertJSONEqual(
            response.content,
            {
                "signing_kp": [message],
                "verification_kp": [message],
                "encryption_kp": [message],
            },
        )

    def test_create_supported_key_type(self):
        """Test an RSA keypair is accepted on every keypair field"""
        cert = create_test_cert()

        response = self.client.post(
            reverse("authentik_api:samlsource-list"),
            data={
                "name": generate_id(),
                "slug": generate_id(),
                "sso_url": "http://localhost",
                "pre_authentication_flow": create_test_flow().pk,
                "signing_kp": cert.pk,
                "verification_kp": cert.pk,
                "encryption_kp": cert.pk,
                "signed_assertion": True,
            },
        )
        self.assertEqual(response.status_code, 201)
