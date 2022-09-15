"""test default login flow"""
from sys import platform
from unittest.case import skipUnless

from authentik.blueprints.tests import apply_blueprint
from tests.e2e.utils import SeleniumTestCase, retry


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestFlowsLogin(SeleniumTestCase):
    """test default login flow"""

    @retry()
    @apply_blueprint(
        "default/10-flow-default-authentication-flow.yaml",
        "default/10-flow-default-invalidation-flow.yaml",
    )
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
        self.assert_user(self.user)
