"""Test userinfo view"""
import json
from dataclasses import asdict

from django.urls import reverse
from django.utils import timezone

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_cert, create_test_flow
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import AccessToken, IDToken, OAuth2Provider, ScopeMapping
from authentik.providers.oauth2.tests.utils import OAuthTestCase


class TestUserinfo(OAuthTestCase):
    """Test token view"""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self) -> None:
        super().setUp()
        self.app = Application.objects.create(name=generate_id(), slug=generate_id())
        self.provider: OAuth2Provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            redirect_uris="",
            signing_key=create_test_cert(),
        )
        self.provider.property_mappings.set(ScopeMapping.objects.all())
        # Needs to be assigned to an application for iss to be set
        self.app.provider = self.provider
        self.app.save()
        self.user = create_test_admin_user()
        self.token: AccessToken = AccessToken.objects.create(
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

    def test_userinfo_normal(self):
        """test user info with all normal scopes"""
        res = self.client.get(
            reverse("authentik_providers_oauth2:userinfo"),
            HTTP_AUTHORIZATION=f"Bearer {self.token.token}",
        )
        self.assertJSONEqual(
            res.content.decode(),
            {
                "name": self.user.name,
                "given_name": self.user.name,
                "preferred_username": self.user.name,
                "nickname": self.user.name,
                "groups": [group.name for group in self.user.ak_groups.all()],
                "sub": "bar",
            },
        )
        self.assertEqual(res.status_code, 200)

    def test_userinfo_invalid_scope(self):
        """test user info with a broken scope"""
        scope = ScopeMapping.objects.create(name="test", scope_name="openid", expression="q")
        self.provider.property_mappings.add(scope)

        res = self.client.get(
            reverse("authentik_providers_oauth2:userinfo"),
            HTTP_AUTHORIZATION=f"Bearer {self.token.token}",
        )
        self.assertJSONEqual(
            res.content.decode(),
            {
                "name": self.user.name,
                "given_name": self.user.name,
                "preferred_username": self.user.name,
                "nickname": self.user.name,
                "groups": [group.name for group in self.user.ak_groups.all()],
                "sub": "bar",
            },
        )
        self.assertEqual(res.status_code, 200)

        events = Event.objects.filter(
            action=EventAction.CONFIGURATION_ERROR,
        )
        self.assertTrue(events.exists())
        self.assertEqual(
            events.first().context["message"],
            "Failed to evaluate property-mapping: 'test'",
        )
