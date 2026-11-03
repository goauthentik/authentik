"""Patreon Type tests"""

from copy import deepcopy
from urllib.parse import parse_qs, urlparse

from django.test import RequestFactory, TestCase
from django.urls import reverse
from requests_mock import Mocker

from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.patreon import PatreonOAuthCallback, PatreonType

PATREON_USER = {
    "data": {
        "attributes": {
            "email": "corgi@example.com",
            "full_name": "Corgi The Dev",
            "vanity": "corgithedev",
        },
        "id": "0000000",
        "type": "user",
    },
}


class TestTypePatreon(TestCase):
    """OAuth Source tests"""

    def setUp(self):
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="patreon",
        )
        self.callback = PatreonOAuthCallback(request=RequestFactory().get("/"))

    def test_enroll_context(self):
        """Test Patreon Enrollment context"""
        ak_context = PatreonType().get_base_user_properties(source=self.source, info=PATREON_USER)
        self.assertEqual(ak_context["username"], PATREON_USER["data"]["attributes"]["vanity"])
        self.assertEqual(ak_context["email"], PATREON_USER["data"]["attributes"]["email"])
        self.assertEqual(ak_context["name"], PATREON_USER["data"]["attributes"]["full_name"])

    def test_enroll_context_without_vanity(self):
        """Patrons without a vanity name still have a stable username."""
        for vanity in [None, ""]:
            with self.subTest(vanity=vanity):
                info = deepcopy(PATREON_USER)
                info["data"]["attributes"]["vanity"] = vanity
                context = PatreonType().get_base_user_properties(info=info)
                self.assertEqual(context["username"], PATREON_USER["data"]["id"])
        info = deepcopy(PATREON_USER)
        del info["data"]["attributes"]["vanity"]
        context = PatreonType().get_base_user_properties(info=info)
        self.assertEqual(context["username"], PATREON_USER["data"]["id"])

    def test_user_id(self):
        """Keep the Patreon user ID used by existing source connections."""
        self.assertEqual(self.callback.get_user_id(PATREON_USER), PATREON_USER["data"]["id"])

    def test_redirect_scopes(self):
        """Request both the v2 identity and email permissions."""
        response = self.client.get(
            reverse("authentik_sources_oauth:oauth-client-login", kwargs={"source_slug": "test"})
        )
        self.assertEqual(response.status_code, 302)
        query = parse_qs(urlparse(response.url).query)
        self.assertEqual(set(query["scope"][0].split()), {"identity", "identity[email]"})

    def test_profile(self):
        """Fetch explicit v2 fields and send the access token only in the header."""
        with Mocker() as mocker:
            mocker.get(
                "https://www.patreon.com/api/oauth2/v2/identity"
                "?fields%5Buser%5D=vanity,email,full_name",
                complete_qs=True,
                request_headers={"Authorization": "Bearer test-token"},
                json=PATREON_USER,
            )
            client = self.callback.get_client(self.source)
            profile = client.get_profile_info(
                {"access_token": "test-token", "token_type": "Bearer"}
            )
        self.assertEqual(profile, PATREON_USER)
        self.assertEqual(self.callback.get_user_id(profile), "0000000")
        context = PatreonType().get_base_user_properties(info=profile)
        self.assertEqual(
            context,
            {"username": "corgithedev", "email": "corgi@example.com", "name": "Corgi The Dev"},
        )

    def test_profile_failure(self):
        """Do not treat a rejected v2 token as a user profile."""
        with Mocker() as mocker:
            mocker.get(
                "https://www.patreon.com/api/oauth2/v2/identity",
                status_code=401,
                json={"errors": [{"status": "401"}]},
            )
            client = self.callback.get_client(self.source)
            self.assertIsNone(
                client.get_profile_info({"access_token": "invalid-token", "token_type": "Bearer"})
            )
