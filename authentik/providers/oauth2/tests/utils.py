"""OAuth test helpers"""
from typing import Any

from django.test import TestCase
from jwt import decode

from authentik.core.tests.utils import create_test_cert
from authentik.crypto.models import CertificateKeyPair
from authentik.providers.oauth2.models import AccessToken, JWTAlgorithms, OAuth2Provider


class OAuthTestCase(TestCase):
    """OAuth test helpers"""

    keypair: CertificateKeyPair
    required_jwt_keys = [
        "exp",
        "iat",
        "acr",
        "sub",
        "iss",
    ]

    @classmethod
    def setUpClass(cls) -> None:
        cls.keypair = create_test_cert()
        super().setUpClass()

    def assert_non_none_or_unset(self, container: dict, key: str):
        """Check that a key, if set, is not none"""
        if key in container:
            self.assertIsNotNone(container[key])

    def validate_jwt(self, token: AccessToken, provider: OAuth2Provider) -> dict[str, Any]:
        """Validate that all required fields are set"""
        key, alg = provider.jwt_key
        if alg != JWTAlgorithms.HS256:
            key = provider.signing_key.public_key
        jwt = decode(
            token.token,
            key,
            algorithms=[alg],
            audience=provider.client_id,
        )
        id_token = token.id_token.to_dict()
        self.assert_non_none_or_unset(id_token, "at_hash")
        self.assert_non_none_or_unset(id_token, "nonce")
        self.assert_non_none_or_unset(id_token, "c_hash")
        self.assert_non_none_or_unset(id_token, "amr")
        self.assert_non_none_or_unset(id_token, "auth_time")
        for key in self.required_jwt_keys:
            self.assertIsNotNone(jwt[key], f"Key {key} is missing in access_token")
            self.assertIsNotNone(id_token[key], f"Key {key} is missing in id_token")
        return jwt
