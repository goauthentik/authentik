"""SCIM OAuth tests"""

from base64 import b64encode
from datetime import timedelta
from urllib.parse import parse_qs, urlencode, urlparse

from django.urls import reverse
from django.utils.timezone import now
from requests_mock import Mocker
from rest_framework.test import APITestCase

from authentik.admin.utils import get_system_settings
from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, User
from authentik.lib.generators import generate_id
from authentik.providers.scim.models import SCIMAuthenticationMode, SCIMMapping, SCIMProvider
from authentik.sources.oauth.models import OAuthSource, UserOAuthSourceConnection
from tests.live import create_test_admin_user


class TestSCIMOAuthToken(APITestCase):
    """SCIM User tests"""

    @apply_blueprint("system/providers-scim.yaml")
    def setUp(self) -> None:
        # Delete all users and groups as the mocked HTTP responses only return one ID
        # which will cause errors with multiple users
        settings = get_system_settings()
        settings.avatars = "none"
        settings.save()
        User.objects.all().exclude_anonymous().delete()
        Group.objects.all().delete()
        self.source = OAuthSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            access_token_url="http://localhost/token",  # nosec
            consumer_key=generate_id(),
            consumer_secret=generate_id(),
            provider_type="openidconnect",
        )
        self.provider = SCIMProvider.objects.create(
            name=generate_id(),
            url="https://localhost",
            auth_mode=SCIMAuthenticationMode.OAUTH_SILENT,
            auth_oauth=self.source,
            auth_oauth_params={
                "foo": "bar",
            },
            exclude_users_service_account=True,
        )
        self.app: Application = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        self.app.backchannel_providers.add(self.provider)
        self.provider.property_mappings.add(
            SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/user")
        )
        self.provider.property_mappings_group.add(
            SCIMMapping.objects.get(managed="goauthentik.io/providers/scim/group")
        )
        self.admin = create_test_admin_user()

    def test_retrieve_token_silent(self):
        """Test token retrieval"""
        with Mocker() as mocker:
            token = generate_id()
            mocker.post("http://localhost/token", json={"access_token": token, "expires_in": 3600})
            self.provider.scim_auth()
        conn = UserOAuthSourceConnection.objects.filter(
            source=self.source,
            user=self.provider.auth_oauth_user,
        ).first()
        self.assertIsNotNone(conn)
        self.assertTrue(conn.is_valid)
        auth = (
            b64encode(
                b":".join((self.source.consumer_key.encode(), self.source.consumer_secret.encode()))
            )
            .strip()
            .decode()
        )
        self.assertEqual(
            mocker.request_history[0].headers["Authorization"],
            f"Basic {auth}",
        )
        self.assertEqual(mocker.request_history[0].body, "grant_type=password&foo=bar")

    def test_retrieve_token_interactive(self):
        """Test token retrieval"""
        self.provider.auth_mode = SCIMAuthenticationMode.OAUTH_INTERACTIVE
        self.provider.save()
        refresh_token = generate_id()
        access_token = generate_id()
        UserOAuthSourceConnection.objects.create(
            user=self.provider.auth_oauth_user,
            source=self.source,
            refresh_token=refresh_token,
            access_token=access_token,
        )
        with Mocker() as mocker:
            token = generate_id()
            mocker.post("http://localhost/token", json={"access_token": token, "expires_in": 3600})
            self.provider.scim_auth()
        conn = UserOAuthSourceConnection.objects.filter(
            source=self.source,
            user=self.provider.auth_oauth_user,
        ).first()
        self.assertEqual(conn.refresh_token, refresh_token)
        self.assertIsNotNone(conn)
        self.assertTrue(conn.is_valid)
        auth = (
            b64encode(
                b":".join((self.source.consumer_key.encode(), self.source.consumer_secret.encode()))
            )
            .strip()
            .decode()
        )
        self.assertEqual(
            mocker.request_history[0].headers["Authorization"],
            f"Basic {auth}",
        )
        self.assertEqual(
            mocker.request_history[0].body,
            f"grant_type=refresh_token&refresh_token={refresh_token}&foo=bar",
        )

    def test_existing_token(self):
        """Test existing token"""
        UserOAuthSourceConnection.objects.create(
            source=self.source,
            user=self.provider.auth_oauth_user,
            access_token=generate_id(),
            expires=now() + timedelta(hours=3),
        )
        with Mocker() as mocker:
            self.provider.scim_auth()
            self.assertEqual(len(mocker.request_history), 0)

    def test_interactive_start(self):
        self.client.force_login(self.admin)
        res = self.client.get(
            reverse(
                "authentik_enterprise_providers_scim:start",
                kwargs={
                    "application_slug": self.app.slug,
                },
            )
        )
        self.assertEqual(res.status_code, 302)
        query = parse_qs(urlparse(res.url).query)
        self.assertEqual(query["client_id"], [self.source.consumer_key])
        self.assertEqual(
            query["redirect_uri"],
            [f"http://testserver/application/scim/{self.app.slug}/oauth2/callback/"],
        )
        self.assertEqual(query["response_type"], ["code"])

    def test_interactive_callback(self):
        self.client.force_login(self.admin)
        res = self.client.get(
            reverse(
                "authentik_enterprise_providers_scim:start",
                kwargs={
                    "application_slug": self.app.slug,
                },
            )
        )
        self.assertEqual(res.status_code, 302)
        query = parse_qs(urlparse(res.url).query)

        with Mocker() as mock:
            token = generate_id()
            mock.post("http://localhost/token", json={"access_token": token, "expires_in": 3600})

            res = self.client.get(
                reverse(
                    "authentik_enterprise_providers_scim:callback",
                    kwargs={
                        "application_slug": self.app.slug,
                    },
                )
                + "?"
                + urlencode({"state": query["state"][0], "code": generate_id()})
            )
            self.assertEqual(res.status_code, 302)

        conn = UserOAuthSourceConnection.objects.filter(source=self.source).first()
        self.assertIsNotNone(conn)
        self.assertTrue(conn.is_valid)
