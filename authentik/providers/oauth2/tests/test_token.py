"""Test token view"""
from base64 import b64encode
from json import dumps

from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id, generate_key
from authentik.providers.oauth2.constants import (
    GRANT_TYPE_AUTHORIZATION_CODE,
    GRANT_TYPE_REFRESH_TOKEN,
    TOKEN_TYPE,
)
from authentik.providers.oauth2.errors import TokenError
from authentik.providers.oauth2.models import (
    AccessToken,
    AuthorizationCode,
    OAuth2Provider,
    RefreshToken,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.views.token import TokenParams


class TestToken(OAuthTestCase):
    """Test token view"""

    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()
        self.app = Application.objects.create(name=generate_id(), slug="test")

    def test_request_auth_code(self):
        """test request param"""
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            redirect_uris="http://TestServer",
            signing_key=self.keypair,
        )
        header = b64encode(f"{provider.client_id}:{provider.client_secret}".encode()).decode()
        user = create_test_admin_user()
        code = AuthorizationCode.objects.create(
            code="foobar", provider=provider, user=user, auth_time=timezone.now()
        )
        request = self.factory.post(
            "/",
            data={
                "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
                "code": code.code,
                "redirect_uri": "http://TestServer",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        params = TokenParams.parse(request, provider, provider.client_id, provider.client_secret)
        self.assertEqual(params.provider, provider)
        with self.assertRaises(TokenError):
            TokenParams.parse(request, provider, provider.client_id, generate_key())

    def test_request_auth_code_invalid(self):
        """test request param"""
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            redirect_uris="http://testserver",
            signing_key=self.keypair,
        )
        header = b64encode(f"{provider.client_id}:{provider.client_secret}".encode()).decode()
        request = self.factory.post(
            "/",
            data={
                "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
                "code": "foo",
                "redirect_uri": "http://testserver",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        with self.assertRaises(TokenError):
            TokenParams.parse(request, provider, provider.client_id, provider.client_secret)

    def test_request_refresh_token(self):
        """test request param"""
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            redirect_uris="http://local.invalid",
            signing_key=self.keypair,
        )
        header = b64encode(f"{provider.client_id}:{provider.client_secret}".encode()).decode()
        user = create_test_admin_user()
        token: RefreshToken = RefreshToken.objects.create(
            provider=provider,
            user=user,
            token=generate_id(),
            auth_time=timezone.now(),
        )
        request = self.factory.post(
            "/",
            data={
                "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                "refresh_token": token.token,
                "redirect_uri": "http://local.invalid",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        params = TokenParams.parse(request, provider, provider.client_id, provider.client_secret)
        self.assertEqual(params.provider, provider)

    def test_auth_code_view(self):
        """test request param"""
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            redirect_uris="http://local.invalid",
            signing_key=self.keypair,
        )
        # Needs to be assigned to an application for iss to be set
        self.app.provider = provider
        self.app.save()
        header = b64encode(f"{provider.client_id}:{provider.client_secret}".encode()).decode()
        user = create_test_admin_user()
        code = AuthorizationCode.objects.create(
            code="foobar", provider=provider, user=user, auth_time=timezone.now()
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
        access: AccessToken = AccessToken.objects.filter(user=user, provider=provider).first()
        refresh: RefreshToken = RefreshToken.objects.filter(user=user, provider=provider).first()
        self.assertJSONEqual(
            response.content.decode(),
            {
                "access_token": access.token,
                "refresh_token": refresh.token,
                "token_type": TOKEN_TYPE,
                "expires_in": 3600,
                "id_token": provider.encode(
                    refresh.id_token.to_dict(),
                ),
            },
        )
        self.validate_jwt(access, provider)

    def test_refresh_token_view(self):
        """test request param"""
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            redirect_uris="http://local.invalid",
            signing_key=self.keypair,
        )
        # Needs to be assigned to an application for iss to be set
        self.app.provider = provider
        self.app.save()
        header = b64encode(f"{provider.client_id}:{provider.client_secret}".encode()).decode()
        user = create_test_admin_user()
        token: RefreshToken = RefreshToken.objects.create(
            provider=provider,
            user=user,
            token=generate_id(),
            _id_token=dumps({}),
            auth_time=timezone.now(),
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                "refresh_token": token.token,
                "redirect_uri": "http://local.invalid",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
            HTTP_ORIGIN="http://local.invalid",
        )
        self.assertEqual(response["Access-Control-Allow-Credentials"], "true")
        self.assertEqual(response["Access-Control-Allow-Origin"], "http://local.invalid")
        access: AccessToken = AccessToken.objects.filter(user=user, provider=provider).first()
        refresh: RefreshToken = RefreshToken.objects.filter(
            user=user, provider=provider, revoked=False
        ).first()
        self.assertJSONEqual(
            response.content.decode(),
            {
                "access_token": access.token,
                "refresh_token": refresh.token,
                "token_type": TOKEN_TYPE,
                "expires_in": 3600,
                "id_token": provider.encode(
                    refresh.id_token.to_dict(),
                ),
            },
        )
        self.validate_jwt(access, provider)

    def test_refresh_token_view_invalid_origin(self):
        """test request param"""
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            redirect_uris="http://local.invalid",
            signing_key=self.keypair,
        )
        header = b64encode(f"{provider.client_id}:{provider.client_secret}".encode()).decode()
        user = create_test_admin_user()
        token: RefreshToken = RefreshToken.objects.create(
            provider=provider,
            user=user,
            token=generate_id(),
            _id_token=dumps({}),
            auth_time=timezone.now(),
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                "refresh_token": token.token,
                "redirect_uri": "http://local.invalid",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
            HTTP_ORIGIN="http://another.invalid",
        )
        access: AccessToken = AccessToken.objects.filter(user=user, provider=provider).first()
        refresh: RefreshToken = RefreshToken.objects.filter(
            user=user, provider=provider, revoked=False
        ).first()
        self.assertNotIn("Access-Control-Allow-Credentials", response)
        self.assertNotIn("Access-Control-Allow-Origin", response)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "access_token": access.token,
                "refresh_token": refresh.token,
                "token_type": TOKEN_TYPE,
                "expires_in": 3600,
                "id_token": provider.encode(
                    refresh.id_token.to_dict(),
                ),
            },
        )

    def test_refresh_token_revoke(self):
        """test request param"""
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            redirect_uris="http://testserver",
            signing_key=self.keypair,
        )
        # Needs to be assigned to an application for iss to be set
        self.app.provider = provider
        self.app.save()
        header = b64encode(f"{provider.client_id}:{provider.client_secret}".encode()).decode()
        user = create_test_admin_user()
        token: RefreshToken = RefreshToken.objects.create(
            provider=provider,
            user=user,
            token=generate_id(),
            _id_token=dumps({}),
            auth_time=timezone.now(),
        )
        # Create initial refresh token
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                "refresh_token": token.token,
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
                "refresh_token": new_token.token,
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
                "refresh_token": new_token.token,
                "redirect_uri": "http://local.invalid",
            },
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Event.objects.filter(action=EventAction.SUSPICIOUS_REQUEST).exists())
