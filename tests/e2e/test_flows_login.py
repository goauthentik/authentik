"""test default login flow"""
from sys import platform
from unittest.case import skipUnless

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from tests.e2e.utils import USER, SeleniumTestCase, retry


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestFlowsLogin(SeleniumTestCase):
    """test default login flow"""

    @retry()
    def test_login(self):
        """test default login flow"""
        self.driver.get(f"{self.live_server_url}/flows/default-authentication-flow/")
        self.driver.find_element(By.ID, "id_uid_field").click()
        self.driver.find_element(By.ID, "id_uid_field").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_uid_field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_password").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        self.wait_for_url(self.shell_url("passbook_core:overview"))
        self.assert_user(USER())
