"""OAuthSource issuer derivation tests"""

from django.test import SimpleTestCase

from authentik.sources.oauth.models import OAuthSource


class TestIssuer(SimpleTestCase):
    """OAuthSource issuer derivation tests"""

    def test_issuer(self):
        for well_known, issuer in [
            # OIDC Discovery: an issuer with a path keeps its trailing slash, an origin has none
            (
                "https://ak.example.com/application/o/app/.well-known/openid-configuration",
                "https://ak.example.com/application/o/app/",
            ),
            ("https://idp.example.com/.well-known/openid-configuration", "https://idp.example.com"),
            # RFC 8414, without and with a path
            (
                "https://as.example.com/.well-known/oauth-authorization-server",
                "https://as.example.com",
            ),
            (
                "https://as.example.com/.well-known/oauth-authorization-server/tenant",
                "https://as.example.com/tenant",
            ),
            ("https://as.example.com/userinfo", None),
            ("", None),
        ]:
            with self.subTest(well_known):
                self.assertEqual(OAuthSource(oidc_well_known_url=well_known).issuer, issuer)
