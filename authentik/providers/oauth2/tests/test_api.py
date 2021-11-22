"""Test oauth2 provider API"""
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.providers.oauth2.models import JWTAlgorithms


class TestOAuth2ProviderAPI(APITestCase):
    """Test oauth2 provider API"""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_validate(self):
        """Test OAuth2 Provider validation"""
        response = self.client.post(
            reverse(
                "authentik_api:oauth2provider-list",
            ),
            data={
                "name": "test",
                "jwt_alg": str(JWTAlgorithms.RS256),
                "authorization_flow": create_test_flow().pk,
            },
        )
        self.assertJSONEqual(
            response.content.decode(),
            {"jwt_alg": ["RS256 requires a Certificate-Key-Pair to be selected."]},
        )
