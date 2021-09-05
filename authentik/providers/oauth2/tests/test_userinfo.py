"""Test userinfo view"""
import json
from dataclasses import asdict

from django.urls import reverse
from django.utils.encoding import force_str

from authentik.core.models import Application, User
from authentik.crypto.models import CertificateKeyPair
from authentik.events.models import Event, EventAction
from authentik.flows.models import Flow
from authentik.lib.generators import generate_id, generate_key
from authentik.managed.manager import ObjectManager
from authentik.providers.oauth2.models import IDToken, OAuth2Provider, RefreshToken, ScopeMapping
from authentik.providers.oauth2.tests.utils import OAuthTestCase


class TestUserinfo(OAuthTestCase):
    """Test token view"""

    def setUp(self) -> None:
        super().setUp()
        ObjectManager().run()
        self.app = Application.objects.create(name="test", slug="test")
        self.provider: OAuth2Provider = OAuth2Provider.objects.create(
            name="test",
            client_id=generate_id(),
            client_secret=generate_key(),
            authorization_flow=Flow.objects.first(),
            redirect_uris="",
            rsa_key=CertificateKeyPair.objects.first(),
        )
        self.provider.property_mappings.set(ScopeMapping.objects.all())
        # Needs to be assigned to an application for iss to be set
        self.app.provider = self.provider
        self.app.save()
        self.user = User.objects.get(username="akadmin")
        self.token: RefreshToken = RefreshToken.objects.create(
            provider=self.provider,
            user=self.user,
            access_token=generate_id(),
            refresh_token=generate_id(),
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
            HTTP_AUTHORIZATION=f"Bearer {self.token.access_token}",
        )
        self.assertJSONEqual(
            force_str(res.content),
            {
                "name": "authentik Default Admin",
                "given_name": "authentik Default Admin",
                "family_name": "",
                "preferred_username": "akadmin",
                "nickname": "akadmin",
                "groups": ["authentik Admins"],
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
            HTTP_AUTHORIZATION=f"Bearer {self.token.access_token}",
        )
        self.assertJSONEqual(
            force_str(res.content),
            {
                "name": "authentik Default Admin",
                "given_name": "authentik Default Admin",
                "family_name": "",
                "preferred_username": "akadmin",
                "nickname": "akadmin",
                "groups": ["authentik Admins"],
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
            "Failed to evaluate property-mapping: name 'q' is not defined",
        )
