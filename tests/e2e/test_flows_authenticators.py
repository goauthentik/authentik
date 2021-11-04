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
from selenium.webdriver.support.wait import WebDriverWait

from authentik.flows.models import Flow, FlowStageBinding
from authentik.stages.authenticator_static.models import AuthenticatorStaticStage
from authentik.stages.authenticator_totp.models import AuthenticatorTOTPStage
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage
from tests.e2e.utils import USER, SeleniumTestCase, apply_migration, retry


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestFlowsAuthenticator(SeleniumTestCase):
    """test flow with otp stages"""

    @retry()
    @apply_migration("authentik_core", "0002_auto_20200523_1133_squashed_0011_provider_name_temp")
    @apply_migration("authentik_flows", "0008_default_flows")
    @apply_migration("authentik_flows", "0011_flow_title")
    def test_totp_validate(self):
        """test flow with otp stages"""
        sleep(1)
        # Setup TOTP Device
        user = USER()
        device = TOTPDevice.objects.create(user=user, confirmed=True, digits=6)

        flow: Flow = Flow.objects.get(slug="default-authentication-flow")
        FlowStageBinding.objects.create(
            target=flow, order=30, stage=AuthenticatorValidateStage.objects.create()
        )

        self.driver.get(self.url("authentik_core:if-flow", flow_slug=flow.slug))
        self.login()

        # Get expected token
        totp = TOTP(device.bin_key, device.step, device.t0, device.digits, device.drift)

        flow_executor = self.get_shadow_root("ak-flow-executor")
        validation_stage = self.get_shadow_root("ak-stage-authenticator-validate", flow_executor)
        code_stage = self.get_shadow_root("ak-stage-authenticator-validate-code", validation_stage)

        code_stage.find_element(By.CSS_SELECTOR, "input[name=code]").send_keys(totp.token())
        code_stage.find_element(By.CSS_SELECTOR, "input[name=code]").send_keys(Keys.ENTER)
        self.wait_for_url(self.if_user_url("/library"))
        self.assert_user(USER())

    @retry()
    @apply_migration("authentik_core", "0002_auto_20200523_1133_squashed_0011_provider_name_temp")
    @apply_migration("authentik_flows", "0008_default_flows")
    @apply_migration("authentik_flows", "0011_flow_title")
    @apply_migration("authentik_stages_authenticator_totp", "0006_default_setup_flow")
    def test_totp_setup(self):
        """test TOTP Setup stage"""
        flow: Flow = Flow.objects.get(slug="default-authentication-flow")

        self.driver.get(self.url("authentik_core:if-flow", flow_slug=flow.slug))
        self.login()

        self.wait_for_url(self.if_user_url("/library"))
        self.assert_user(USER())

        self.driver.get(
            self.url(
                "authentik_flows:configure",
                stage_uuid=AuthenticatorTOTPStage.objects.first().stage_uuid,
            )
        )

        flow_executor = self.get_shadow_root("ak-flow-executor")
        totp_stage = self.get_shadow_root("ak-stage-authenticator-totp", flow_executor)
        wait = WebDriverWait(totp_stage, self.wait_timeout)

        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "input[name=otp_uri]")))
        otp_uri = totp_stage.find_element(By.CSS_SELECTOR, "input[name=otp_uri]").get_attribute(
            "value"
        )

        # Parse the OTP URI, extract the secret and get the next token
        otp_args = urlparse(otp_uri)
        self.assertEqual(otp_args.scheme, "otpauth")
        otp_qs = parse_qs(otp_args.query)
        secret_key = b32decode(otp_qs["secret"][0])

        totp = TOTP(secret_key)

        totp_stage.find_element(By.CSS_SELECTOR, "input[name=code]").send_keys(totp.token())
        totp_stage.find_element(By.CSS_SELECTOR, "input[name=code]").send_keys(Keys.ENTER)
        sleep(3)

        self.assertTrue(TOTPDevice.objects.filter(user=USER(), confirmed=True).exists())

    @retry()
    @apply_migration("authentik_core", "0002_auto_20200523_1133_squashed_0011_provider_name_temp")
    @apply_migration("authentik_flows", "0008_default_flows")
    @apply_migration("authentik_flows", "0011_flow_title")
    @apply_migration("authentik_stages_authenticator_static", "0005_default_setup_flow")
    def test_static_setup(self):
        """test Static OTP Setup stage"""
        flow: Flow = Flow.objects.get(slug="default-authentication-flow")

        self.driver.get(self.url("authentik_core:if-flow", flow_slug=flow.slug))
        self.login()

        self.wait_for_url(self.if_user_url("/library"))
        self.assert_user(USER())

        self.driver.get(
            self.url(
                "authentik_flows:configure",
                stage_uuid=AuthenticatorStaticStage.objects.first().stage_uuid,
            )
        )

        # Remember the current URL as we should end up back here
        destination_url = self.driver.current_url

        flow_executor = self.get_shadow_root("ak-flow-executor")
        authenticator_stage = self.get_shadow_root("ak-stage-authenticator-static", flow_executor)
        token = authenticator_stage.find_element(By.CSS_SELECTOR, "ul li:nth-child(1)").text

        authenticator_stage.find_element(By.CSS_SELECTOR, "button[type=submit]").click()

        self.wait_for_url(destination_url)
        sleep(1)

        self.assertTrue(StaticDevice.objects.filter(user=USER(), confirmed=True).exists())
        device = StaticDevice.objects.filter(user=USER(), confirmed=True).first()
        self.assertTrue(StaticToken.objects.filter(token=token, device=device).exists())
