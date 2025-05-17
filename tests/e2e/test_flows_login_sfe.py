"""test default login (using SFE interface) flow"""

from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from authentik.blueprints.tests import apply_blueprint
from tests.e2e.utils import SeleniumTestCase, retry


class TestFlowsLoginSFE(SeleniumTestCase):
    """test default login flow"""

    def login(self):
        """Do entire login flow adjusted for SFE"""
        flow_executor = self.driver.find_element(By.ID, "flow-sfe-container")
        identification_stage = flow_executor.find_element(By.ID, "ident-form")

        identification_stage.find_element(By.CSS_SELECTOR, "input[name=uid_field]").click()
        identification_stage.find_element(By.CSS_SELECTOR, "input[name=uid_field]").send_keys(
            self.user.username
        )
        identification_stage.find_element(By.CSS_SELECTOR, "input[name=uid_field]").send_keys(
            Keys.ENTER
        )

        password_stage = flow_executor.find_element(By.ID, "password-form")
        password_stage.find_element(By.CSS_SELECTOR, "input[name=password]").send_keys(
            self.user.username
        )
        password_stage.find_element(By.CSS_SELECTOR, "input[name=password]").send_keys(Keys.ENTER)
        sleep(1)

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
        self.login()
        self.wait_for_url(self.if_user_url("/library"))
        self.assert_user(self.user)
