"""test flow with otp stages"""
from base64 import b32decode
from sys import platform
from time import sleep
from unittest.case import skipUnless
from urllib.parse import parse_qs, urlparse

from django_otp.oath import TOTP
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec

from e2e.utils import USER, SeleniumTestCase
from passbook.flows.models import Flow, FlowStageBinding
from passbook.stages.otp_validate.models import OTPValidateStage


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestFlowsOTP(SeleniumTestCase):
    """test flow with otp stages"""

    def test_otp_validate(self):
        """test flow with otp stages"""
        sleep(1)
        # Setup TOTP Device
        user = USER()
        device = TOTPDevice.objects.create(user=user, confirmed=True, digits=6)

        flow: Flow = Flow.objects.get(slug="default-authentication-flow")
        # Move the user_login stage to order 3
        FlowStageBinding.objects.filter(target=flow, order=2).update(order=3)
        FlowStageBinding.objects.create(
            target=flow, order=2, stage=OTPValidateStage.objects.create()
        )

        self.driver.get(f"{self.live_server_url}/flows/{flow.slug}/")
        self.driver.find_element(By.ID, "id_uid_field").click()
        self.driver.find_element(By.ID, "id_uid_field").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_uid_field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_password").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)

        # Get expected token
        totp = TOTP(device.bin_key, device.step, device.t0, device.digits, device.drift)
        self.driver.find_element(By.ID, "id_code").send_keys(totp.token())
        self.driver.find_element(By.ID, "id_code").send_keys(Keys.ENTER)
        self.wait_for_url(self.url("passbook_core:overview"))
        self.assertEqual(
            self.driver.find_element(By.ID, "user-settings").text, USER().username,
        )

    def test_otp_totp_setup(self):
        """test TOTP Setup stage"""
        flow: Flow = Flow.objects.get(slug="default-authentication-flow")

        self.driver.get(f"{self.live_server_url}/flows/{flow.slug}/")
        self.driver.find_element(By.ID, "id_uid_field").click()
        self.driver.find_element(By.ID, "id_uid_field").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_uid_field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_password").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        self.assertEqual(
            self.driver.find_element(By.ID, "user-settings").text, USER().username,
        )

        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-page__header").click()
        self.driver.get(self.url("passbook_core:user-settings"))

        self.driver.find_element(By.LINK_TEXT, "Time-based OTP").click()

        # Remember the current URL as we should end up back here
        destination_url = self.driver.current_url

        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-card__body a.pf-c-button"
        ).click()

        self.wait.until(ec.presence_of_element_located((By.ID, "qr")))
        otp_uri = self.driver.find_element(By.ID, "qr").get_attribute("data-otpuri")

        # Parse the OTP URI, extract the secret and get the next token
        otp_args = urlparse(otp_uri)
        self.assertEqual(otp_args.scheme, "otpauth")
        otp_qs = parse_qs(otp_args.query)
        secret_key = b32decode(otp_qs["secret"][0])

        totp = TOTP(secret_key)

        self.driver.find_element(By.ID, "id_code").send_keys(totp.token())
        self.driver.find_element(By.ID, "id_code").send_keys(Keys.ENTER)

        self.wait_for_url(destination_url)
        sleep(1)

        self.assertTrue(TOTPDevice.objects.filter(user=USER(), confirmed=True).exists())

    def test_otp_static_setup(self):
        """test Static OTP Setup stage"""
        flow: Flow = Flow.objects.get(slug="default-authentication-flow")

        self.driver.get(f"{self.live_server_url}/flows/{flow.slug}/")
        self.driver.find_element(By.ID, "id_uid_field").click()
        self.driver.find_element(By.ID, "id_uid_field").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_uid_field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_password").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        self.assertEqual(
            self.driver.find_element(By.ID, "user-settings").text, USER().username,
        )

        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-page__header").click()
        self.driver.find_element(By.ID, "user-settings").click()
        self.wait_for_url(self.url("passbook_core:user-settings"))

        self.driver.find_element(By.LINK_TEXT, "Static OTP").click()

        # Remember the current URL as we should end up back here
        destination_url = self.driver.current_url

        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-card__body a.pf-c-button"
        ).click()
        token = self.driver.find_element(
            By.CSS_SELECTOR, ".pb-otp-tokens li:nth-child(1)"
        ).text

        self.driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()

        self.wait_for_url(destination_url)
        sleep(1)

        self.assertTrue(
            StaticDevice.objects.filter(user=USER(), confirmed=True).exists()
        )
        device = StaticDevice.objects.filter(user=USER(), confirmed=True).first()
        self.assertTrue(StaticToken.objects.filter(token=token, device=device).exists())
