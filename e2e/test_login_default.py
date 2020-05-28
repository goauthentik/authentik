"""test default login flow"""
import string
from random import SystemRandom

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys

from passbook.core.models import User


class TestLogin(StaticLiveServerTestCase):
    """test default login flow"""

    host = "0.0.0.0"
    port = 8000

    def setUp(self):
        self.driver = webdriver.Remote(
            command_executor="http://localhost:4444/wd/hub",
            desired_capabilities=DesiredCapabilities.CHROME,
        )
        self.driver.implicitly_wait(2)
        self.password = "".join(
            SystemRandom().choice(string.ascii_uppercase + string.digits)
            for _ in range(8)
        )
        User.objects.create_superuser(
            username="pbadmin", email="admin@example.tld", password=self.password
        )
        call_command("migrate", "--fake", "passbook_flows", "0001_initial")
        call_command("migrate", "passbook_flows", "0002_default_flows")

    def tearDown(self):
        super().tearDown()
        self.driver.quit()

    def test_login(self):
        """test default login flow"""
        self.driver.get(
            f"http://host.docker.internal:{self.port}/flows/default-authentication-flow/?next=%2F"
        )
        self.driver.find_element(By.ID, "id_uid_field").click()
        self.driver.find_element(By.ID, "id_uid_field").send_keys("admin@example.tld")
        self.driver.find_element(By.ID, "id_uid_field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_password").send_keys(self.password)
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        self.assertEqual(
            self.driver.find_element(By.XPATH, "//a[contains(@href, '/-/user/')]").text,
            "pbadmin",
        )
