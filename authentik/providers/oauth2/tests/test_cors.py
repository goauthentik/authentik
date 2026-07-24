"""Test OAuth2 CORS handling"""

from django.http import HttpResponse
from django.test import RequestFactory

from authentik.providers.oauth2.models import RedirectURI, RedirectURIMatchingMode
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.utils import cors_allow, origin_matches_redirect_uri


class TestCORS(OAuthTestCase):
    """Test CORS origin matching for redirect URIs"""

    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()

    def test_origin_matches_redirect_uri_strict(self):
        """Test strict redirect URI origin matching"""
        redirect = RedirectURI(
            RedirectURIMatchingMode.STRICT,
            "https://preview-skypilot-pr-69-fundash.g3rg.org/auth/callback",
        )
        self.assertTrue(
            origin_matches_redirect_uri(
                "https://preview-skypilot-pr-69-fundash.g3rg.org",
                redirect,
            )
        )
        self.assertFalse(
            origin_matches_redirect_uri(
                "https://preview-other-pr-1-fundash.g3rg.org",
                redirect,
            )
        )

    def test_origin_matches_redirect_uri_regex(self):
        """Test regex redirect URI origin matching"""
        redirect = RedirectURI(
            RedirectURIMatchingMode.REGEX,
            r"https://preview-.*-fundash\.g3rg\.org/auth/callback",
        )
        self.assertTrue(
            origin_matches_redirect_uri(
                "https://preview-skypilot-pr-69-fundash.g3rg.org",
                redirect,
            )
        )

    def test_origin_matches_redirect_uri_regex_no_match(self):
        """Test regex redirect URI rejects non-matching origins"""
        redirect = RedirectURI(
            RedirectURIMatchingMode.REGEX,
            r"https://preview-.*-fundash\.g3rg\.org/auth/callback",
        )
        self.assertFalse(
            origin_matches_redirect_uri(
                "https://malicious.example.org",
                redirect,
            )
        )

    def test_cors_allow_sets_headers_for_regex(self):
        """Test cors_allow adds headers when regex redirect URI matches origin"""
        redirect = RedirectURI(
            RedirectURIMatchingMode.REGEX,
            r"https://preview-.*-fundash\.g3rg\.org/auth/callback",
        )
        request = self.factory.post(
            "/application/o/token/",
            HTTP_ORIGIN="https://preview-skypilot-pr-69-fundash.g3rg.org",
        )
        response = HttpResponse()
        cors_allow(request, response, redirect)
        self.assertEqual(
            response["Access-Control-Allow-Origin"],
            "https://preview-skypilot-pr-69-fundash.g3rg.org",
        )
        self.assertEqual(response["Access-Control-Allow-Credentials"], "true")

    def test_cors_allow_no_headers_for_regex_mismatch(self):
        """Test cors_allow omits headers when origin does not match"""
        redirect = RedirectURI(
            RedirectURIMatchingMode.REGEX,
            r"https://preview-.*-fundash\.g3rg\.org/auth/callback",
        )
        request = self.factory.post(
            "/application/o/token/",
            HTTP_ORIGIN="https://malicious.example.org",
        )
        response = HttpResponse()
        cors_allow(request, response, redirect)
        self.assertNotIn("Access-Control-Allow-Origin", response)

    def test_cors_allow_options_without_redirect_uris(self):
        """Test OPTIONS preflight is allowed without redirect URI checks"""
        request = self.factory.options(
            "/application/o/token/",
            HTTP_ORIGIN="https://preview-skypilot-pr-69-fundash.g3rg.org",
        )
        response = HttpResponse()
        cors_allow(request, response)
        self.assertEqual(
            response["Access-Control-Allow-Origin"],
            "https://preview-skypilot-pr-69-fundash.g3rg.org",
        )
