"""OAuth test helpers"""
from django.test import TestCase
from jwt import decode

from authentik.providers.oauth2.models import JWTAlgorithms, OAuth2Provider, RefreshToken


class OAuthTestCase(TestCase):
    """OAuth test helpers"""

    required_jwt_keys = [
        "exp",
        "iat",
        "auth_time",
        "acr",
        "sub",
        "iss",
    ]

    def validate_jwt(self, token: RefreshToken, provider: OAuth2Provider):
        """Validate that all required fields are set"""
        key = provider.client_secret
        if provider.jwt_alg == JWTAlgorithms.RS256:
            key = provider.rsa_key.public_key
        jwt = decode(
            token.access_token,
            key,
            algorithms=[provider.jwt_alg],
            audience=provider.client_id,
        )
        id_token = token.id_token.to_dict()
        for key in self.required_jwt_keys:
            self.assertIsNotNone(jwt[key], f"Key {key} is missing in access_token")
            self.assertIsNotNone(id_token[key], f"Key {key} is missing in id_token")
