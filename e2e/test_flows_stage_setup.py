"""test stage setup flows (password change)"""
import string
from random import SystemRandom
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from e2e.utils import USER, SeleniumTestCase
from passbook.core.models import User


class TestFlowsStageSetup(SeleniumTestCase):
    """test stage setup flows"""

    def test_password_change(self):
        """test password change flow"""
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
