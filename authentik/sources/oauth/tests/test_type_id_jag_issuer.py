"""Identity Assertion Issuer source type tests"""

from django.test import RequestFactory
from django.urls import reverse
from requests_mock import Mocker
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id
from authentik.sources.oauth.models import IdJagUserMatching, OAuthSource

ISSUER = "https://identity.example.com/issuers/a1b2c3"
METADATA_URL = f"{ISSUER}/.well-known/openid-configuration"
JWKS_URL = f"{ISSUER}/jwks"
JWKS = {"keys": [{"kty": "EC", "crv": "P-256", "x": "x", "y": "y", "kid": "k1"}]}


class TestTypeIdJagIssuer(APITestCase):
    """An issuer of ID-JAGs that users don't sign in through"""

    def setUp(self):
        self.client.force_login(create_test_admin_user())
        self.requests = Mocker()
        self.requests.start()
        self.addCleanup(self.requests.stop)
        # Only what an issuer that only signs assertions publishes
        self.metadata = self.requests.get(
            METADATA_URL, json={"issuer": ISSUER, "jwks_uri": JWKS_URL}
        )
        self.requests.get(JWKS_URL, json=JWKS)

    def create(self, **data):
        return self.client.post(
            reverse("authentik_api:oauthsource-list"),
            {
                "name": generate_id(),
                "slug": generate_id(),
                "provider_type": "idjagissuer",
                "id_jag_issuer": ISSUER,
                "id_jag_email_domains": ["corp.example"],
                **data,
            },
            format="json",
        )

    def test_create(self):
        """Only the issuer and email domains are needed; its metadata and keys are found
        from the issuer"""
        response = self.create()
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.data["id_jag_issuer"], ISSUER)
        source = OAuthSource.objects.get(slug=response.data["slug"])
        self.assertEqual(source.oidc_well_known_url, METADATA_URL)
        self.assertEqual(source.oidc_jwks_url, JWKS_URL)
        self.assertEqual(source.oidc_jwks, JWKS)
        self.assertEqual(source.consumer_key, "")
        self.assertEqual(source.id_jag_issuer, ISSUER)
        self.assertEqual(source.id_jag_user_matching, IdJagUserMatching.EMAIL)

    def test_create_invalid(self):
        """The issuer must be an https URL whose metadata names it, with keys, and some
        email domain must be trusted, as users are found by email"""
        for data in (
            {"id_jag_issuer": ""},
            {"id_jag_issuer": "http://identity.example.com/issuers/a1b2c3"},
            {"id_jag_issuer": f"{ISSUER}?tenant=a"},
            {"id_jag_issuer": "https://user:pass@identity.example.com/issuers/a1b2c3"},
            {"id_jag_issuer": "https://identity.example.com/.well-known/openid-configuration"},
            {
                "id_jag_issuer": "https://identity.example.com/a/.well-known/oauth-authorization-server"
            },
            {"id_jag_email_domains": []},
            {"id_jag_user_matching": IdJagUserMatching.IDENTIFIER},
        ):
            with self.subTest(data=data):
                response = self.create(**data)
                self.assertEqual(response.status_code, 400, response.content)
        self.metadata = self.requests.get(
            METADATA_URL, json={"issuer": "https://identity.example.com/", "jwks_uri": JWKS_URL}
        )
        response = self.create()
        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("id_jag_issuer", response.data)
        self.requests.get(METADATA_URL, json={"issuer": ISSUER})
        response = self.create()
        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("id_jag_issuer", response.data)

    def test_issuer_exact(self):
        """The metadata's issuer must equal the entered one exactly, trailing slash included,
        and the issuer is stored as entered"""
        slash = f"{ISSUER}/"
        # Metadata at the same URL, whichever way the issuer is entered (Discovery §4)
        self.requests.get(METADATA_URL, json={"issuer": slash, "jwks_uri": JWKS_URL})
        response = self.create()
        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("id_jag_issuer", response.data)
        response = self.create(id_jag_issuer=slash)
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.data["id_jag_issuer"], slash)
        source = OAuthSource.objects.get(slug=response.data["slug"])
        self.assertEqual(source.id_jag_issuer, slash)
        self.assertEqual(source.oidc_well_known_url, METADATA_URL)
        # Saving it again keeps validating against the stored issuer
        response = self.client.patch(
            reverse("authentik_api:oauthsource-detail", kwargs={"slug": source.slug}),
            {"name": generate_id()},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data["id_jag_issuer"], slash)
        # And the other way round
        self.requests.get(METADATA_URL, json={"issuer": ISSUER, "jwks_uri": JWKS_URL})
        response = self.create(id_jag_issuer=slash)
        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("id_jag_issuer", response.data)

    def test_login_sources_need_client(self):
        """Other types still need a consumer key"""
        response = self.client.post(
            reverse("authentik_api:oauthsource-list"),
            {
                "name": generate_id(),
                "slug": generate_id(),
                "provider_type": "discord",
                "consumer_secret": generate_id(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("consumer_key", response.data)

    def test_no_login(self):
        """Users can't sign in through it, or connect to it in their settings"""
        response = self.create()
        source = OAuthSource.objects.get(slug=response.data["slug"])
        self.assertIsNone(source.ui_login_button(RequestFactory().get("/")))
        self.assertIsNone(source.ui_user_settings())
        for name in ("oauth-client-login", "oauth-client-callback"):
            with self.subTest(view=name):
                response = self.client.get(
                    reverse(f"authentik_sources_oauth:{name}", kwargs={"source_slug": source.slug})
                )
                self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("authentik_api:source-user-settings"))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(source.slug, [setting["object_uid"] for setting in response.data])
