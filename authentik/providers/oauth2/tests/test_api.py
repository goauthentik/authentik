"""Test oauth2 provider API"""
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.flows.models import Flow, FlowDesignation
from authentik.providers.oauth2.models import JWTAlgorithms


class TestOAuth2ProviderAPI(APITestCase):
    """Test oauth2 provider API"""

    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.get(username="akadmin")
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
                "authorization_flow": Flow.objects.filter(designation=FlowDesignation.AUTHORIZATION)
                .first()
                .pk,
            },
        )
        self.assertJSONEqual(
            response.content.decode(),
            {"jwt_alg": ["RS256 requires a Certificate-Key-Pair to be selected."]},
        )
