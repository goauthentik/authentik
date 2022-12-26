"""OAuth test helpers"""
from typing import Any

from django.test import TestCase
from jwt import decode

from authentik.core.tests.utils import create_test_cert
from authentik.crypto.models import CertificateKeyPair
from authentik.providers.oauth2.models import JWTAlgorithms, OAuth2Provider, RefreshToken


class OAuthTestCase(TestCase):
    """OAuth test helpers"""

    keypair: CertificateKeyPair
    required_jwt_keys = [
        "exp",
        "iat",
        "auth_time",
        "acr",
        "sub",
        "iss",
    ]

    @classmethod
    def setUpClass(cls) -> None:
        cls.keypair = create_test_cert()
        super().setUpClass()

    def validate_jwt(self, token: RefreshToken, provider: OAuth2Provider) -> dict[str, Any]:
        """Validate that all required fields are set"""
        key, alg = provider.jwt_key
        if alg != JWTAlgorithms.HS256:
            key = provider.signing_key.public_key
        jwt = decode(
            token.access_token,
            key,
            algorithms=[alg],
            audience=provider.client_id,
        )
        id_token = token.id_token.to_dict()
        for key in self.required_jwt_keys:
            self.assertIsNotNone(jwt[key], f"Key {key} is missing in access_token")
            self.assertIsNotNone(id_token[key], f"Key {key} is missing in id_token")
        return jwt
