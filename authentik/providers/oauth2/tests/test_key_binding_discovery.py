"""Test OpenID Connect Key Binding discovery metadata"""

from django.urls import reverse

from authentik.blueprints.models import BlueprintInstance
from authentik.blueprints.v1.importer import Importer
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import OAuth2Provider, ScopeMapping
from authentik.providers.oauth2.tests.utils import OAuthTestCase


class TestKeyBindingDiscovery(OAuthTestCase):
    """Test discovery metadata includes key binding support"""

    def setUp(self) -> None:
        super().setUp()
        content = BlueprintInstance(path="system/providers-oauth2.yaml").retrieve()
        Importer.from_string(content).apply()
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id="test",
            authorization_flow=create_test_flow(),
            signing_key=self.keypair,
        )
        self.provider.property_mappings.set(
            ScopeMapping.objects.filter(
                managed__in=[
                    "goauthentik.io/providers/oauth2/scope-openid",
                    "goauthentik.io/providers/oauth2/scope-bound_key",
                ]
            )
        )
        self.app = Application.objects.create(
            name=generate_id(), slug="test", provider=self.provider
        )

    def test_discovery_includes_bound_key(self):
        """scopes_supported should include bound_key"""
        response = self.client.get(
            reverse(
                "authentik_providers_oauth2:provider-info",
                kwargs={"application_slug": self.app.slug},
            )
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("scopes_supported", body)
        self.assertIn("bound_key", body["scopes_supported"])

    def test_discovery_includes_dpop_algs(self):
        """dpop_signing_alg_values_supported should be present"""
        response = self.client.get(
            reverse(
                "authentik_providers_oauth2:provider-info",
                kwargs={"application_slug": self.app.slug},
            )
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("dpop_signing_alg_values_supported", body)
        self.assertIsInstance(body["dpop_signing_alg_values_supported"], list)
        self.assertGreater(len(body["dpop_signing_alg_values_supported"]), 0)
