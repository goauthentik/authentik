"""test default login flow"""
from sys import platform
from unittest.case import skipUnless

from tests.e2e.utils import USER, SeleniumTestCase, apply_migration, retry


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestFlowsLogin(SeleniumTestCase):
    """test default login flow"""

    @retry()
    @apply_migration("authentik_core", "0003_default_user")
    @apply_migration("authentik_flows", "0008_default_flows")
    def test_login(self):
        """test default login flow"""
        self.driver.get(f"{self.live_server_url}/flows/default-authentication-flow/")
        self.login()
        self.wait_for_url(self.shell_url("/library"))
        self.assert_user(USER())
