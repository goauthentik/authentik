"""test default login flow"""
from sys import platform
from unittest.case import skipUnless

from tests.e2e.utils import USER, SeleniumTestCase, apply_migration, retry


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestFlowsLogin(SeleniumTestCase):
    """test default login flow"""

    @retry()
    @apply_migration("authentik_core", "0002_auto_20200523_1133_squashed_0011_provider_name_temp")
    @apply_migration("authentik_flows", "0008_default_flows")
    @apply_migration("authentik_flows", "0011_flow_title")
    def test_login(self):
        """test default login flow"""
        self.driver.get(
            self.url(
                "authentik_core:if-flow",
                flow_slug="default-authentication-flow",
            )
        )
        self.login()
        self.wait_for_url(self.if_user_url("/library"))
        self.assert_user(USER())
