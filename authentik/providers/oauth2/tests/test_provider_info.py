"""Provider info (OpenID discovery) tests"""

from unittest.mock import patch

from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application
from authentik.core.tests.utils import RequestFactory, create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import (
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    ScopeMapping,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.views.provider import ProviderInfoView, claims_cache_key


class TestProviderInfo(OAuthTestCase):
    """Test provider info view"""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self) -> None:
        super().setUp()
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id=generate_id(),
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid")],
            signing_key=self.keypair,
        )
        self.provider.property_mappings.set(ScopeMapping.objects.all())
        self.app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.provider
        )

    def get_info(self, app: Application | None = None) -> dict:
        """Fetch the discovery document"""
        response = self.client.get(
            reverse(
                "authentik_providers_oauth2:provider-info",
                kwargs={"application_slug": (app or self.app).slug},
            )
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_info(self):
        """Test discovery document"""
        body = self.get_info()
        self.assertTrue(body["issuer"].endswith(f"/application/o/{self.app.slug}/"))
        self.assertTrue(body["token_endpoint"].endswith("/token/"))
        self.assertIn("openid", body["scopes_supported"])
        self.assertIn("email", body["scopes_supported"])
        for claim in ["sub", "iss", "aud", "exp", "iat", "acr", "amr", "nonce"]:
            self.assertIn(claim, body["claims_supported"])
        # Claims from the default scope mappings
        self.assertIn("email", body["claims_supported"])
        self.assertIn("preferred_username", body["claims_supported"])

    def test_claims_cached(self):
        """Test claims are only evaluated once"""
        claims = self.get_info()["claims_supported"]
        # Anything hitting get_claims again means the cache didn't take
        with patch.object(ProviderInfoView, "get_claims", return_value=claims) as get_claims:
            self.assertEqual(self.get_info()["claims_supported"], claims)
        get_claims.assert_not_called()

    def test_claims_cached_per_provider(self):
        """Test cached claims aren't shared between providers"""
        self.get_info()
        other = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id=generate_id(),
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid")],
            signing_key=self.keypair,
        )
        other.property_mappings.set(
            ScopeMapping.objects.filter(managed="goauthentik.io/providers/oauth2/scope-openid")
        )
        other_app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=other
        )
        self.assertNotIn("email", self.get_info(other_app)["claims_supported"])
        self.assertIn("email", self.get_info()["claims_supported"])

    def test_claims_mapping_error(self):
        """Test failing scope mapping is skipped"""
        self.provider.property_mappings.add(
            ScopeMapping.objects.create(
                name=generate_id(),
                scope_name=generate_id(),
                expression="raise Exception('test')",
            )
        )
        body = self.get_info()
        self.assertIn("email", body["claims_supported"])

    def test_private_key_not_loaded(self):
        """Test the signing algorithm is read without loading the private key, whose validation
        is slow for RSA keys"""
        with patch("authentik.crypto.models._load_private_key", side_effect=AssertionError):
            body = self.get_info()
        self.assertEqual(body["id_token_signing_alg_values_supported"], ["RS256"])

    def test_queries(self):
        """Test a request with cached claims loads the application, provider and keys in one
        query"""
        self.get_info()
        request = RequestFactory().get("/")
        # provider, scope names, cached claims and dynamic client registration
        with self.assertNumQueries(4):
            response = ProviderInfoView.as_view()(request, application_slug=self.app.slug)
        self.assertEqual(response.status_code, 200)

    def test_claims_queries(self):
        """Test evaluating the claims does not query once per scope mapping"""
        request = RequestFactory().get("/")

        def count_queries() -> int:
            cache.delete(claims_cache_key(self.provider))
            with CaptureQueriesContext(connection) as ctx:
                ProviderInfoView.as_view()(request, application_slug=self.app.slug)
            return len(ctx.captured_queries)

        def mapping() -> ScopeMapping:
            return ScopeMapping.objects.create(
                name=generate_id(), scope_name=generate_id(), expression="return {'claim': 1}"
            )

        self.provider.property_mappings.set([mapping()])
        one = count_queries()
        self.provider.property_mappings.add(mapping(), mapping(), mapping())
        self.assertEqual(count_queries(), one)
