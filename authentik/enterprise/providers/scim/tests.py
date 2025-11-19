"""SCIM OAuth tests"""

from base64 import b64encode
from datetime import timedelta
from unittest.mock import MagicMock, PropertyMock, patch

from django.urls import reverse
from django.utils.timezone import now
from requests_mock import Mocker
from rest_framework.test import APITestCase

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, User
from authentik.core.tests.utils import create_test_admin_user
from authentik.enterprise.license import LicenseKey
from authentik.enterprise.models import License
from authentik.enterprise.tests.test_license import expiry_valid
from authentik.lib.generators import generate_id
from authentik.providers.scim.models import SCIMAuthenticationMode, SCIMMapping, SCIMProvider
from authentik.sources.oauth.models import OAuthSource, UserOAuthSourceConnection
from authentik.tenants.models import Tenant


class SCIMOAuthTests(APITestCase):
    """SCIM User tests"""

    @apply_blueprint("system/providers-scim.yaml")
    def setUp(self) -> None:
        # Delete all users and groups as the mocked HTTP responses only return one ID
        # which will cause errors with multiple users
        Tenant.objects.update(avatars="none")
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
            auth_mode=SCIMAuthenticationMode.OAUTH,
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

    def test_retrieve_token(self):
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

    @Mocker()
    def test_user_create(self, mock: Mocker):
        """Test user creation"""
        scim_id = generate_id()
        token = generate_id()
        mock.post("http://localhost/token", json={"access_token": token, "expires_in": 3600})
        mock.get(
            "https://localhost/ServiceProviderConfig",
            json={},
        )
        mock.post(
            "https://localhost/Users",
            json={
                "id": scim_id,
            },
        )
        uid = generate_id()
        user = User.objects.create(
            username=uid,
            name=f"{uid} {uid}",
            email=f"{uid}@goauthentik.io",
        )
        self.assertEqual(mock.call_count, 3)
        self.assertEqual(mock.request_history[1].method, "GET")
        self.assertEqual(mock.request_history[2].method, "POST")
        self.assertJSONEqual(
            mock.request_history[2].body,
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "active": True,
                "emails": [
                    {
                        "primary": True,
                        "type": "other",
                        "value": f"{uid}@goauthentik.io",
                    }
                ],
                "externalId": user.uid,
                "name": {
                    "familyName": uid,
                    "formatted": f"{uid} {uid}",
                    "givenName": uid,
                },
                "displayName": f"{uid} {uid}",
                "userName": uid,
            },
        )

    @patch(
        "authentik.enterprise.license.LicenseKey.validate",
        MagicMock(
            return_value=LicenseKey(
                aud="",
                exp=expiry_valid,
                name=generate_id(),
                internal_users=100,
                external_users=100,
            )
        ),
    )
    def test_api_create(self):
        License.objects.create(key=generate_id())
        self.client.force_login(create_test_admin_user())
        res = self.client.post(
            reverse("authentik_api:scimprovider-list"),
            {
                "name": generate_id(),
                "url": "http://localhost",
                "auth_mode": "oauth",
                "auth_oauth": str(self.source.pk),
            },
        )
        self.assertEqual(res.status_code, 201)

    @patch(
        "authentik.enterprise.models.LicenseUsageStatus.is_valid",
        PropertyMock(return_value=False),
    )
    def test_api_create_no_license(self):
        self.client.force_login(create_test_admin_user())
        res = self.client.post(
            reverse("authentik_api:scimprovider-list"),
            {
                "name": generate_id(),
                "url": "http://localhost",
                "auth_mode": "oauth",
                "auth_oauth": str(self.source.pk),
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(
            res.content, {"auth_mode": ["Enterprise is required to use the OAuth mode."]}
        )
