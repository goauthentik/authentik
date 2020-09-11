"""test stage setup flows (password change)"""
import string
from random import SystemRandom
from sys import platform
from time import sleep
from unittest.case import skipUnless

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from e2e.utils import USER, SeleniumTestCase
from passbook.core.models import User
from passbook.flows.models import Flow, FlowDesignation
from passbook.stages.password.models import PasswordStage


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestFlowsStageSetup(SeleniumTestCase):
    """test stage setup flows"""

    def test_password_change(self):
        """test password change flow"""
        # Ensure that password stage has change_flow set
        flow = Flow.objects.get(
            slug="default-password-change", designation=FlowDesignation.STAGE_SETUP,
        )

        stages = PasswordStage.objects.filter(name="default-authentication-password")
        stage = stages.first()
        stage.change_flow = flow
        stage.save()

        new_password = "".join(
            SystemRandom().choice(string.ascii_uppercase + string.digits)
            for _ in range(8)
        )

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

        sleep(2)
        # Because USER() is cached, we need to get the user manually here
        user = User.objects.get(username=USER().username)
        self.assertTrue(user.check_password(new_password))
