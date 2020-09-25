"""test stage setup flows (password change)"""
from sys import platform
from unittest.case import skipUnless

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from e2e.utils import USER, SeleniumTestCase
from passbook.core.models import User
from passbook.flows.models import Flow, FlowDesignation
from passbook.providers.oauth2.generators import generate_client_secret
from passbook.stages.password.models import PasswordStage


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestFlowsStageSetup(SeleniumTestCase):
    """test stage setup flows"""

    def test_password_change(self):
        """test password change flow"""
        # Ensure that password stage has change_flow set
        flow = Flow.objects.get(
            slug="default-password-change", designation=FlowDesignation.STAGE_CONFIGURATION,
        )

        stage = PasswordStage.objects.get(name="default-authentication-password")
        stage.configure_flow = flow
        stage.save()

        new_password = generate_client_secret()

        self.driver.get(
            f"{self.live_server_url}/flows/default-authentication-flow/?next=%2F"
        )
        self.driver.find_element(By.ID, "id_uid_field").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_uid_field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_password").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-page__header").click()
        self.driver.find_element(By.XPATH, "//a[contains(@href, '/-/user/')]").click()
        self.wait_for_url(self.url("passbook_core:user-settings"))
        self.driver.find_element(By.LINK_TEXT, "Change password").click()
        self.driver.find_element(By.ID, "id_password").send_keys(new_password)
        self.driver.find_element(By.ID, "id_password_repeat").click()
        self.driver.find_element(By.ID, "id_password_repeat").send_keys(new_password)
        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-button").click()

        self.wait_for_url(self.url("passbook_core:user-settings"))
        # Because USER() is cached, we need to get the user manually here
        user = User.objects.get(username=USER().username)
        self.assertTrue(user.check_password(new_password))
