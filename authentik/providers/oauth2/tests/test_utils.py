"""Test OAuth2 utility helpers"""

from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from authentik.providers.oauth2.models import RedirectURI, RedirectURIMatchingMode
from authentik.providers.oauth2.utils import cors_allow


class TestCorsAllow(TestCase):
    """Tests for ``cors_allow``: ensures regex-mode redirect URI entries are honoured
    for CORS origin validation, not only for the authorize-step redirect_uri check."""

    def setUp(self):
        self.factory = RequestFactory()

    def _post(self, origin: str):
        return self.factory.post("/", HTTP_ORIGIN=origin)

    def test_strict_match(self):
        """Strict origin entry matches scheme + host + port (regression)."""
        request = self._post("http://local.invalid")
        response = cors_allow(
            request,
            HttpResponse(),
            RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid/callback"),
        )
        self.assertEqual(response["Access-Control-Allow-Origin"], "http://local.invalid")
        self.assertEqual(response["Access-Control-Allow-Credentials"], "true")

    def test_strict_no_match(self):
        """Strict entry on a different host does not allow the origin."""
        request = self._post("http://other.invalid")
        response = cors_allow(
            request,
            HttpResponse(),
            RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid/callback"),
        )
        self.assertNotIn("Access-Control-Allow-Origin", response)

    def test_regex_match(self):
        """Regex entry matching the Origin sets the CORS header."""
        request = self._post("https://app-abc123.example.com")
        response = cors_allow(
            request,
            HttpResponse(),
            RedirectURI(
                RedirectURIMatchingMode.REGEX,
                r"https://app-\w+\.example\.com",
            ),
        )
        self.assertEqual(response["Access-Control-Allow-Origin"], "https://app-abc123.example.com")

    def test_regex_no_match(self):
        """Regex entry that does not match the Origin must not allow the request."""
        request = self._post("https://evil.example.com")
        response = cors_allow(
            request,
            HttpResponse(),
            RedirectURI(
                RedirectURIMatchingMode.REGEX,
                r"https://app-\w+\.example\.com",
            ),
        )
        self.assertNotIn("Access-Control-Allow-Origin", response)

    def test_regex_with_optional_path_group(self):
        """A regex written as ``host(/path)?`` should match the bare Origin (without path)
        as well as the full redirect URI used by the authorize step."""
        regex = r"https://app-\w+\.example\.com(/callback)?"
        # Origin (no path)
        response = cors_allow(
            self._post("https://app-foo.example.com"),
            HttpResponse(),
            RedirectURI(RedirectURIMatchingMode.REGEX, regex),
        )
        self.assertEqual(response["Access-Control-Allow-Origin"], "https://app-foo.example.com")
        # Origin equal to a wrong host: must not match.
        response = cors_allow(
            self._post("https://other.example.com"),
            HttpResponse(),
            RedirectURI(RedirectURIMatchingMode.REGEX, regex),
        )
        self.assertNotIn("Access-Control-Allow-Origin", response)

    def test_regex_full_redirect_uri_does_not_match_bare_origin(self):
        """A regex written for the full redirect URI (including a mandatory path) will
        not match a bare Origin header. This is the documented behaviour: users wanting
        regex CORS support should write ``host(/path)?`` or add a separate origin entry."""
        request = self._post("https://app-abc.example.com")
        response = cors_allow(
            request,
            HttpResponse(),
            RedirectURI(
                RedirectURIMatchingMode.REGEX,
                r"https://app-\w+\.example\.com/callback",
            ),
        )
        self.assertNotIn("Access-Control-Allow-Origin", response)

    def test_malformed_regex_is_skipped(self):
        """Malformed regexes are logged and skipped; a later valid entry still matches."""
        request = self._post("https://good.example.com")
        response = cors_allow(
            request,
            HttpResponse(),
            RedirectURI(RedirectURIMatchingMode.REGEX, r"["),  # invalid regex
            RedirectURI(RedirectURIMatchingMode.REGEX, r"https://good\.example\.com"),
        )
        self.assertEqual(response["Access-Control-Allow-Origin"], "https://good.example.com")

    def test_malformed_regex_alone_does_not_500(self):
        """A malformed regex with no other allowed entries must return the response
        unchanged rather than raising."""
        request = self._post("https://anything.example.com")
        response = cors_allow(
            request,
            HttpResponse(),
            RedirectURI(RedirectURIMatchingMode.REGEX, r"["),
        )
        self.assertNotIn("Access-Control-Allow-Origin", response)

    def test_options_request_allowed_without_match(self):
        """Pre-flight OPTIONS requests are allowed through without an entry match
        (regression: existing behaviour)."""
        request = self.factory.options(
            "/",
            HTTP_ORIGIN="https://anywhere.example.com",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type",
        )
        response = cors_allow(request, HttpResponse())
        self.assertEqual(response["Access-Control-Allow-Origin"], "https://anywhere.example.com")

    def test_bare_string_treated_as_strict(self):
        """Backwards compatibility: bare string entries are treated as STRICT."""
        request = self._post("http://local.invalid")
        response = cors_allow(request, HttpResponse(), "http://local.invalid/callback")
        self.assertEqual(response["Access-Control-Allow-Origin"], "http://local.invalid")

    def test_mixed_strict_and_regex(self):
        """A provider with one strict and one regex entry honours both."""
        entries = (
            RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid/callback"),
            RedirectURI(RedirectURIMatchingMode.REGEX, r"https://app-\w+\.example\.com"),
        )
        # Strict origin matches via the strict entry.
        response = cors_allow(self._post("http://local.invalid"), HttpResponse(), *entries)
        self.assertEqual(response["Access-Control-Allow-Origin"], "http://local.invalid")
        # Regex origin matches via the regex entry.
        response = cors_allow(self._post("https://app-xyz.example.com"), HttpResponse(), *entries)
        self.assertEqual(response["Access-Control-Allow-Origin"], "https://app-xyz.example.com")
