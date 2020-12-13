"""Test authorize view"""
from django.test import RequestFactory, TestCase

from authentik.flows.models import Flow
from authentik.providers.oauth2.errors import (
    AuthorizeError,
    ClientIdError,
    RedirectUriError,
)
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.providers.oauth2.views.authorize import OAuthAuthorizationParams


class TestViewsAuthorize(TestCase):
    """Test authorize view"""

    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()

    def test_invalid_grant_type(self):
        """Test with invalid grant type"""
        with self.assertRaises(AuthorizeError):
            request = self.factory.get("/", data={"response_type": "invalid"})
            OAuthAuthorizationParams.from_request(request)

    def test_invalid_client_id(self):
        """Test invalid client ID"""
        with self.assertRaises(ClientIdError):
            request = self.factory.get(
                "/", data={"response_type": "code", "client_id": "invalid"}
            )
            OAuthAuthorizationParams.from_request(request)

    def test_missing_redirect_uri(self):
        """test missing redirect URI"""
        OAuth2Provider.objects.create(
            name="test",
            client_id="test",
            authorization_flow=Flow.objects.first(),
        )
        with self.assertRaises(RedirectUriError):
            request = self.factory.get(
                "/", data={"response_type": "code", "client_id": "test"}
            )
            OAuthAuthorizationParams.from_request(request)
