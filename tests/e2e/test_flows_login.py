"""test default login flow"""

from authentik.blueprints.tests import apply_blueprint
from authentik.flows.models import Flow
from tests.e2e.utils import SeleniumTestCase, retry


class TestFlowsLogin(SeleniumTestCase):
    """test default login flow"""

    def tearDown(self):
        # Reset authentication flow's compatibility mode; we need to do this as its
        # not specified in the blueprint
        Flow.objects.filter(slug="default-authentication-flow").update(compatibility_mode=False)
        return super().tearDown()

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
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

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    def test_login_compatibility_mode(self):
        """test default login flow with compatibility mode enabled"""
        Flow.objects.filter(slug="default-authentication-flow").update(compatibility_mode=True)
        self.driver.get(
            self.url(
                "authentik_core:if-flow",
                flow_slug="default-authentication-flow",
            )
        )
        self.login(shadow_dom=False)
        self.wait_for_url(self.if_user_url("/library"))
        self.assert_user(self.user)
