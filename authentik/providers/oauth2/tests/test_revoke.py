"""Test revoke view"""

import json
from base64 import b64encode
from dataclasses import asdict

from django.urls import reverse
from django.utils import timezone

from authentik.core.models import Application, AuthenticatedSession, Session
from authentik.core.tests.utils import create_test_admin_user, create_test_cert, create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import (
    AccessToken,
    ClientTypes,
    DeviceToken,
    IDToken,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    RefreshToken,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.root.middleware import ClientIPMiddleware


class TesOAuth2Revoke(OAuthTestCase):
    """Test revoke view"""

    def setUp(self) -> None:
        super().setUp()
        self.provider: OAuth2Provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "")],
            signing_key=create_test_cert(),
        )
        self.app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.provider
        )
        self.app.save()
        self.user = create_test_admin_user()
        self.auth = b64encode(
            f"{self.provider.client_id}:{self.provider.client_secret}".encode()
        ).decode()

    def test_revoke_refresh(self):
        """Test revoke"""
        token: RefreshToken = RefreshToken.objects.create(
            provider=self.provider,
            user=self.user,
            token=generate_id(),
            auth_time=timezone.now(),
            _scope="openid user profile",
            _id_token=json.dumps(
                asdict(
                    IDToken("foo", "bar"),
                )
            ),
        )
        res = self.client.post(
            reverse("authentik_providers_oauth2:token-revoke"),
            HTTP_AUTHORIZATION=f"Basic {self.auth}",
            data={
                "token": token.token,
            },
        )
        self.assertEqual(res.status_code, 200)

    def test_revoke_access(self):
        """Test revoke"""
        token: AccessToken = AccessToken.objects.create(
            provider=self.provider,
            user=self.user,
            token=generate_id(),
            auth_time=timezone.now(),
            _scope="openid user profile",
            _id_token=json.dumps(
                asdict(
                    IDToken("foo", "bar"),
                )
            ),
        )
        res = self.client.post(
            reverse("authentik_providers_oauth2:token-revoke"),
            HTTP_AUTHORIZATION=f"Basic {self.auth}",
            data={
                "token": token.token,
            },
        )
        self.assertEqual(res.status_code, 200)

    def test_revoke_invalid(self):
        """Test revoke (invalid token)"""
        res = self.client.post(
            reverse("authentik_providers_oauth2:token-revoke"),
            HTTP_AUTHORIZATION=f"Basic {self.auth}",
            data={
                "token": generate_id(),
            },
        )
        self.assertEqual(res.status_code, 200)

    def test_revoke_invalid_auth(self):
        """Test revoke (invalid auth)"""
        res = self.client.post(
            reverse("authentik_providers_oauth2:token-revoke"),
            HTTP_AUTHORIZATION="Basic fqewr",
            data={
                "token": generate_id(),
            },
        )
        self.assertEqual(res.status_code, 401)

    def test_revoke_public(self):
        """Test revoke public client"""
        self.provider.client_type = ClientTypes.PUBLIC
        self.provider.save()
        token: AccessToken = AccessToken.objects.create(
            provider=self.provider,
            user=self.user,
            token=generate_id(),
            auth_time=timezone.now(),
            _scope="openid user profile",
            _id_token=json.dumps(
                asdict(
                    IDToken("foo", "bar"),
                )
            ),
        )
        auth_public = b64encode(f"{self.provider.client_id}:{generate_id()}".encode()).decode()
        res = self.client.post(
            reverse("authentik_providers_oauth2:token-revoke"),
            HTTP_AUTHORIZATION=f"Basic {auth_public}",
            data={
                "token": token.token,
            },
        )
        self.assertEqual(res.status_code, 200)

    def test_revoke_logout(self):
        """Test revoke on logout"""
        self.client.force_login(self.user)
        AccessToken.objects.create(
            provider=self.provider,
            user=self.user,
            session=self.client.session["authenticatedsession"],
            token=generate_id(),
            auth_time=timezone.now(),
            _scope="openid user profile",
            _id_token=json.dumps(
                asdict(
                    IDToken("foo", "bar"),
                )
            ),
        )
        self.client.logout()
        self.assertEqual(AccessToken.objects.all().count(), 0)

    def test_revoke_session_delete(self):
        """Test revoke on logout"""
        session = AuthenticatedSession.objects.create(
            session=Session.objects.create(
                session_key=generate_id(),
                last_ip=ClientIPMiddleware.default_ip,
            ),
            user=self.user,
        )
        AccessToken.objects.create(
            provider=self.provider,
            user=self.user,
            session=session,
            token=generate_id(),
            auth_time=timezone.now(),
            _scope="openid user profile",
            _id_token=json.dumps(
                asdict(
                    IDToken("foo", "bar"),
                )
            ),
        )
        session.delete()
        self.assertEqual(AccessToken.objects.all().count(), 0)

    def test_revoke_user_deactivated(self):
        """Test revoke on logout"""
        AccessToken.objects.create(
            provider=self.provider,
            user=self.user,
            token=generate_id(),
            auth_time=timezone.now(),
            _scope="openid user profile",
            _id_token=json.dumps(
                asdict(
                    IDToken("foo", "bar"),
                )
            ),
        )
        RefreshToken.objects.create(
            provider=self.provider,
            user=self.user,
            token=generate_id(),
            auth_time=timezone.now(),
            _scope="openid user profile",
            _id_token=json.dumps(
                asdict(
                    IDToken("foo", "bar"),
                )
            ),
        )
        DeviceToken.objects.create(
            provider=self.provider,
            user=self.user,
            _scope="openid user profile",
        )

        self.user.is_active = False
        self.user.save()

        self.assertEqual(AccessToken.objects.all().count(), 0)
        self.assertEqual(RefreshToken.objects.all().count(), 0)
        self.assertEqual(DeviceToken.objects.all().count(), 0)
