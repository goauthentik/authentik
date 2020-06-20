"""test default login flow"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys

from e2e.utils import SeleniumTestCase


class TestLogin(SeleniumTestCase):
    """test default login flow"""

    def test_login(self):
        """test default login flow"""
        self.driver.get(f"{self.live_server_url}/flows/default-authentication-flow/")
        self.driver.find_element(By.ID, "id_uid_field").click()
        self.driver.find_element(By.ID, "id_uid_field").send_keys("pbadmin")
        self.driver.find_element(By.ID, "id_uid_field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_password").send_keys("pbadmin")
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        self.assertEqual(
            self.driver.find_element(By.XPATH, "//a[contains(@href, '/-/user/')]").text,
            "pbadmin",
        )
