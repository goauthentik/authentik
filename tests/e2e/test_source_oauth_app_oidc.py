"""test OAuth Source login into an OAuth2/OIDC application"""

from json import dumps

from authentik.core.models import User
from tests.e2e.oauth_source import OIDCAppMixin, SourceAppRedirectMixin
from tests.selenium import SeleniumTestCase


class TestSourceOAuthAppOIDC(OIDCAppMixin, SourceAppRedirectMixin, SeleniumTestCase):
    """test OAuth Source login into an OAuth2/OIDC application"""

    def assert_app_login(self, user: User, entry_uri: str):
        body = self.parse_json_content()
        snippet = dumps(body, indent=2)[:500].replace("\n", " ")
        claims = body.get("IDTokenClaims", {})

        for key, expected, actual in (
            ("IDTokenClaims.nickname", user.username, claims.get("nickname")),
            ("IDTokenClaims.email", user.email, claims.get("email")),
            ("InitialURL", entry_uri, body.get("InitialURL")),
        ):
            self.assertEqual(
                actual, expected, f"{key} mismatch at {self.driver.current_url}: {snippet}"
            )
