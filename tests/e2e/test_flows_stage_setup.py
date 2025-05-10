"""test stage setup flows (password change)"""

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import User
from authentik.crypto.generators import generate_key
from authentik.flows.models import Flow, FlowDesignation
from authentik.stages.password.models import PasswordStage
from tests.e2e.utils import SeleniumTestCase, retry


class TestFlowsStageSetup(SeleniumTestCase):
    """test stage setup flows"""

    @retry()
    @apply_blueprint("default/flow-password-change.yaml")
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    def test_password_change(self):
        """test password change flow"""
        # Ensure that password stage has change_flow set
        flow = Flow.objects.get(
            slug="default-password-change",
            designation=FlowDesignation.STAGE_CONFIGURATION,
        )

        stage = PasswordStage.objects.get(name="default-authentication-password")
        stage.configure_flow = flow
        stage.save()

        new_password = generate_key()

        self.driver.get(
            self.url(
                "authentik_core:if-flow",
                flow_slug="default-authentication-flow",
            )
        )
        self.login()
        self.wait_for_url(self.if_user_url("/library"))

        self.driver.get(
            self.url(
                "authentik_flows:configure",
                stage_uuid=PasswordStage.objects.first().stage_uuid,
            )
        )

        flow_executor = self.get_shadow_root("ak-flow-executor")
        prompt_stage = self.get_shadow_root("ak-stage-prompt", flow_executor)

        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=password]").send_keys(new_password)
        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=password_repeat]").send_keys(
            new_password
        )
        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=password_repeat]").send_keys(
            Keys.ENTER
        )

        self.wait_for_url(self.if_user_url("/library"))
        # Because self.user is cached, we need to get the user manually here
        user = User.objects.get(username=self.user.username)
        self.assertTrue(user.check_password(new_password))
