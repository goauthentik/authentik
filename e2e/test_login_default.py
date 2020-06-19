"""test default login flow"""
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys

from e2e.utils import apply_default_data


class TestLogin(StaticLiveServerTestCase):
    """test default login flow"""

    def setUp(self):
        self.driver = webdriver.Remote(
            command_executor="http://localhost:4444/wd/hub",
            desired_capabilities=DesiredCapabilities.CHROME,
        )
        self.driver.implicitly_wait(5)
        apply_default_data()

    def tearDown(self):
        super().tearDown()
        self.driver.quit()

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
