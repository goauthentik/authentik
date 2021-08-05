"""Test token view"""
from base64 import b64encode

from django.test import RequestFactory
from django.urls import reverse
from django.utils.encoding import force_str

from authentik.core.models import Application, User
from authentik.crypto.models import CertificateKeyPair
from authentik.events.models import Event, EventAction
from authentik.flows.models import Flow
from authentik.providers.oauth2.constants import (
    GRANT_TYPE_AUTHORIZATION_CODE,
    GRANT_TYPE_REFRESH_TOKEN,
)
from authentik.providers.oauth2.generators import generate_client_id, generate_client_secret
from authentik.providers.oauth2.models import AuthorizationCode, OAuth2Provider, RefreshToken
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.views.token import TokenParams


class TestToken(OAuthTestCase):
    """Test token view"""

    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()
        self.app = Application.objects.create(name="test", slug="test")

    def test_request_auth_code(self):
        """test request param"""
        provider = OAuth2Provider.objects.create(
            name="test",
            client_id=generate_client_id(),
            client_secret=generate_client_secret(),
            authorization_flow=Flow.objects.first(),
            redirect_uris="http://testserver",
            rsa_key=CertificateKeyPair.objects.first(),
        )
        header = b64encode(f"{provider.client_id}:{provider.client_secret}".encode()).decode()
        user = User.objects.get(username="akadmin")
        code = AuthorizationCode.objects.create(code="foobar", provider=provider, user=user)
        request = self.factory.post(
            "/",
            data={
                "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
                "code": code.code,
                "redirect_uri": "http://testserver",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        params = TokenParams.parse(request, provider, provider.client_id, provider.client_secret)
        self.assertEqual(params.provider, provider)

    def test_request_refresh_token(self):
        """test request param"""
        provider = OAuth2Provider.objects.create(
            name="test",
            client_id=generate_client_id(),
            client_secret=generate_client_secret(),
            authorization_flow=Flow.objects.first(),
            redirect_uris="http://local.invalid",
            rsa_key=CertificateKeyPair.objects.first(),
        )
        header = b64encode(f"{provider.client_id}:{provider.client_secret}".encode()).decode()
        user = User.objects.get(username="akadmin")
        token: RefreshToken = RefreshToken.objects.create(
            provider=provider,
            user=user,
            refresh_token=generate_client_id(),
        )
        request = self.factory.post(
            "/",
            data={
                "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                "refresh_token": token.refresh_token,
                "redirect_uri": "http://local.invalid",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        params = TokenParams.parse(request, provider, provider.client_id, provider.client_secret)
        self.assertEqual(params.provider, provider)

    def test_auth_code_view(self):
        """test request param"""
        provider = OAuth2Provider.objects.create(
            name="test",
            client_id=generate_client_id(),
            client_secret=generate_client_secret(),
            authorization_flow=Flow.objects.first(),
            redirect_uris="http://local.invalid",
            rsa_key=CertificateKeyPair.objects.first(),
        )
        # Needs to be assigned to an application for iss to be set
        self.app.provider = provider
        self.app.save()
        header = b64encode(f"{provider.client_id}:{provider.client_secret}".encode()).decode()
        user = User.objects.get(username="akadmin")
        code = AuthorizationCode.objects.create(
            code="foobar", provider=provider, user=user, is_open_id=True
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
                "code": code.code,
                "redirect_uri": "http://local.invalid",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        new_token: RefreshToken = RefreshToken.objects.filter(user=user).first()
        self.assertJSONEqual(
            force_str(response.content),
            {
                "access_token": new_token.access_token,
                "refresh_token": new_token.refresh_token,
                "token_type": "bearer",
                "expires_in": 600,
                "id_token": provider.encode(
                    new_token.id_token.to_dict(),
                ),
            },
        )
        self.validate_jwt(new_token, provider)

    def test_refresh_token_view(self):
        """test request param"""
        provider = OAuth2Provider.objects.create(
            name="test",
            client_id=generate_client_id(),
            client_secret=generate_client_secret(),
            authorization_flow=Flow.objects.first(),
            redirect_uris="http://local.invalid",
            rsa_key=CertificateKeyPair.objects.first(),
        )
        # Needs to be assigned to an application for iss to be set
        self.app.provider = provider
        self.app.save()
        header = b64encode(f"{provider.client_id}:{provider.client_secret}".encode()).decode()
        user = User.objects.get(username="akadmin")
        token: RefreshToken = RefreshToken.objects.create(
            provider=provider,
            user=user,
            refresh_token=generate_client_id(),
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                "refresh_token": token.refresh_token,
                "redirect_uri": "http://local.invalid",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
            HTTP_ORIGIN="http://local.invalid",
        )
        new_token: RefreshToken = (
            RefreshToken.objects.filter(user=user).exclude(pk=token.pk).first()
        )
        self.assertEqual(response["Access-Control-Allow-Credentials"], "true")
        self.assertEqual(response["Access-Control-Allow-Origin"], "http://local.invalid")
        self.assertJSONEqual(
            force_str(response.content),
            {
                "access_token": new_token.access_token,
                "refresh_token": new_token.refresh_token,
                "token_type": "bearer",
                "expires_in": 600,
                "id_token": provider.encode(
                    new_token.id_token.to_dict(),
                ),
            },
        )
        self.validate_jwt(new_token, provider)

    def test_refresh_token_view_invalid_origin(self):
        """test request param"""
        provider = OAuth2Provider.objects.create(
            name="test",
            client_id=generate_client_id(),
            client_secret=generate_client_secret(),
            authorization_flow=Flow.objects.first(),
            redirect_uris="http://local.invalid",
            rsa_key=CertificateKeyPair.objects.first(),
        )
        header = b64encode(f"{provider.client_id}:{provider.client_secret}".encode()).decode()
        user = User.objects.get(username="akadmin")
        token: RefreshToken = RefreshToken.objects.create(
            provider=provider,
            user=user,
            refresh_token=generate_client_id(),
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                "refresh_token": token.refresh_token,
                "redirect_uri": "http://local.invalid",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
            HTTP_ORIGIN="http://another.invalid",
        )
        new_token: RefreshToken = (
            RefreshToken.objects.filter(user=user).exclude(pk=token.pk).first()
        )
        self.assertNotIn("Access-Control-Allow-Credentials", response)
        self.assertNotIn("Access-Control-Allow-Origin", response)
        self.assertJSONEqual(
            force_str(response.content),
            {
                "access_token": new_token.access_token,
                "refresh_token": new_token.refresh_token,
                "token_type": "bearer",
                "expires_in": 600,
                "id_token": provider.encode(
                    new_token.id_token.to_dict(),
                ),
            },
        )

    def test_refresh_token_revoke(self):
        """test request param"""
        provider = OAuth2Provider.objects.create(
            name="test",
            client_id=generate_client_id(),
            client_secret=generate_client_secret(),
            authorization_flow=Flow.objects.first(),
            redirect_uris="http://testserver",
            rsa_key=CertificateKeyPair.objects.first(),
        )
        # Needs to be assigned to an application for iss to be set
        self.app.provider = provider
        self.app.save()
        header = b64encode(f"{provider.client_id}:{provider.client_secret}".encode()).decode()
        user = User.objects.get(username="akadmin")
        token: RefreshToken = RefreshToken.objects.create(
            provider=provider,
            user=user,
            refresh_token=generate_client_id(),
        )
        # Create initial refresh token
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                "refresh_token": token.refresh_token,
                "redirect_uri": "http://testserver",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        new_token: RefreshToken = (
            RefreshToken.objects.filter(user=user).exclude(pk=token.pk).first()
        )
        # Post again with initial token -> get new refresh token
        # and revoke old one
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                "refresh_token": new_token.refresh_token,
                "redirect_uri": "http://local.invalid",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        self.assertEqual(response.status_code, 200)
        # Post again with old token, is now revoked and should error
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                "refresh_token": new_token.refresh_token,
                "redirect_uri": "http://local.invalid",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Event.objects.filter(action=EventAction.SUSPICIOUS_REQUEST).exists())
