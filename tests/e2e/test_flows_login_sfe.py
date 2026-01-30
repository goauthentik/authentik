"""test default login (using SFE interface) flow"""

from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import User
from authentik.flows.models import NotConfiguredAction
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage, DeviceClasses
from tests.e2e.utils import SeleniumTestCase, retry


def login_sfe(driver: WebDriver, user: User):
    """Do entire login flow adjusted for SFE"""
    flow_executor = driver.find_element(By.ID, "flow-sfe-container")
    identification_stage = flow_executor.find_element(By.ID, "ident-form")

    identification_stage.find_element(By.CSS_SELECTOR, "input[name=uid_field]").click()
    identification_stage.find_element(By.CSS_SELECTOR, "input[name=uid_field]").send_keys(
        user.username
    )
    identification_stage.find_element(By.CSS_SELECTOR, "input[name=uid_field]").send_keys(
        Keys.ENTER
    )

    password_stage = flow_executor.find_element(By.ID, "password-form")
    password_stage.find_element(By.CSS_SELECTOR, "input[name=password]").send_keys(user.username)
    password_stage.find_element(By.CSS_SELECTOR, "input[name=password]").send_keys(Keys.ENTER)
    sleep(1)


class TestFlowsLoginSFE(SeleniumTestCase):
    """test default login flow"""

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
                query={"sfe": True},
            )
        )
        login_sfe(self.driver, self.user)
        self.wait_for_url(self.if_user_url("/library"))
        self.assert_user(self.user)

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    def test_login_mfa_static_deny(self):
        """test default login flow"""
        mfa = AuthenticatorValidateStage.objects.get(
            name="default-authentication-mfa-validation",
        )
        mfa.not_configured_action = NotConfiguredAction.DENY
        mfa.device_classes = [DeviceClasses.STATIC]
        mfa.save()

        self.driver.get(
            self.url(
                "authentik_core:if-flow",
                flow_slug="default-authentication-flow",
                query={"sfe": True},
            )
        )
        login_sfe(self.driver, self.user)
        msg = self.driver.find_element(By.CSS_SELECTOR, "#access-denied > p")
        self.assertEqual(msg.text, "No (allowed) MFA authenticator configured.")
