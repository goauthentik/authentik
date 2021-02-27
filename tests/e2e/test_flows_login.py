"""test default login flow"""
from sys import platform
from unittest.case import skipUnless

from tests.e2e.utils import USER, SeleniumTestCase, retry


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestFlowsLogin(SeleniumTestCase):
    """test default login flow"""

    @retry()
    def test_login(self):
        """test default login flow"""
        self.driver.get(f"{self.live_server_url}/flows/default-authentication-flow/")
        self.login()
        self.wait_for_url(self.shell_url("/library"))
        self.assert_user(USER())
