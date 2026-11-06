"""WS-Federation Provider API tests"""

from unittest import skipIf

from cryptography.hazmat.backends.openssl.backend import backend
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_cert, create_test_flow
from authentik.crypto.builder import PrivateKeyAlg
from authentik.lib.generators import generate_id


class TestWSFederationProviderAPI(APITestCase):
    """WS-Federation Provider API tests"""

    def setUp(self) -> None:
        super().setUp()
        self.client.force_login(create_test_admin_user())

    @skipIf(backend._fips_enabled, "The FIPS provider has no Ed25519")
    def test_create_validate_unsupported_key_type(self):
        """Test validation rejects key types without an XML-DSIG transform (Ed25519)"""
        ed25519_cert = create_test_cert(PrivateKeyAlg.ED25519)

        response = self.client.post(
            reverse("authentik_api:wsfederationprovider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                "reply_url": "http://localhost",
                "wtrealm": generate_id(),
                "signing_kp": ed25519_cert.pk,
                "encryption_kp": ed25519_cert.pk,
                "sign_assertion": True,
            },
        )
        self.assertEqual(response.status_code, 400)
        message = (
            "Key type Ed25519 is not supported. Supported key types are: RSA, Elliptic Curve, DSA."
        )
        self.assertJSONEqual(
            response.content,
            {"signing_kp": [message], "encryption_kp": [message]},
        )
