"""Test Enroll flow"""
from time import sleep

from django.test import override_settings
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import User
from authentik.flows.models import Flow
from authentik.stages.identification.models import IdentificationStage
from tests.e2e.utils import SeleniumTestCase, retry


class TestFlowsEnroll(SeleniumTestCase):
    """Test Enroll flow"""

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "example/flows-enrollment-2-stage.yaml",
    )
    def test_enroll_2_step(self):
        """Test 2-step enroll flow"""
        # Attach enrollment flow to identification stage
        ident_stage: IdentificationStage = IdentificationStage.objects.get(
            name="default-authentication-identification"
        )
        ident_stage.enrollment_flow = Flow.objects.get(slug="default-enrollment-flow")
        ident_stage.save()

        self.driver.get(self.live_server_url)

        self.initial_stages()

        interface_user = self.get_shadow_root("ak-interface-user")
        wait = WebDriverWait(interface_user, self.wait_timeout)

        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, ".pf-c-page__header")))
        self.driver.get(self.if_user_url("/settings"))

        user = User.objects.get(username="foo")
        self.assertEqual(user.username, "foo")
        self.assertEqual(user.name, "some name")
        self.assertEqual(user.email, "foo@bar.baz")

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "example/flows-enrollment-email-verification.yaml",
    )
    @override_settings(EMAIL_PORT=1025)
    def test_enroll_email(self):
        """Test enroll with Email verification"""
        # Attach enrollment flow to identification stage
        ident_stage: IdentificationStage = IdentificationStage.objects.get(
            name="default-authentication-identification"
        )
        ident_stage.enrollment_flow = Flow.objects.get(slug="default-enrollment-flow")
        ident_stage.save()

        self.driver.get(self.live_server_url)
        self.initial_stages()

        # Email stage
        flow_executor = self.get_shadow_root("ak-flow-executor")
        email_stage = self.get_shadow_root("ak-stage-email", flow_executor)

        wait = WebDriverWait(email_stage, self.wait_timeout)

        # Wait for the success message so we know the email is sent
        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, ".pf-c-form p")))

        # Open Mailpit
        self.driver.get("http://localhost:8025")

        # Click on first message
        self.wait.until(ec.presence_of_element_located((By.CLASS_NAME, "message")))
        self.driver.find_element(By.CLASS_NAME, "message").click()
        self.driver.switch_to.frame(self.driver.find_element(By.ID, "preview-html"))
        self.driver.find_element(By.ID, "confirm").click()
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

        sleep(2)
        # We're now logged in
        wait = WebDriverWait(self.get_shadow_root("ak-interface-user"), self.wait_timeout)

        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, ".pf-c-page__header")))
        self.driver.get(self.if_user_url("/settings"))

        self.assert_user(User.objects.get(username="foo"))

    def initial_stages(self):
        """Fill out initial stages"""
        # Identification stage, click enroll
        flow_executor = self.get_shadow_root("ak-flow-executor")
        identification_stage = self.get_shadow_root("ak-stage-identification", flow_executor)
        wait = WebDriverWait(identification_stage, self.wait_timeout)

        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "#enroll")))
        identification_stage.find_element(By.CSS_SELECTOR, "#enroll").click()

        # First prompt stage
        flow_executor = self.get_shadow_root("ak-flow-executor")
        prompt_stage = self.get_shadow_root("ak-stage-prompt", flow_executor)
        wait = WebDriverWait(prompt_stage, self.wait_timeout)

        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "input[name=username]")))
        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=username]").send_keys("foo")
        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=password]").send_keys(
            self.user.username
        )
        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=password_repeat]").send_keys(
            self.user.username
        )
        prompt_stage.find_element(By.CSS_SELECTOR, ".pf-c-button").click()

        # Second prompt stage
        flow_executor = self.get_shadow_root("ak-flow-executor")
        prompt_stage = self.get_shadow_root("ak-stage-prompt", flow_executor)
        wait = WebDriverWait(prompt_stage, self.wait_timeout)

        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "input[name=name]")))
        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=name]").send_keys("some name")
        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=email]").send_keys("foo@bar.baz")
        prompt_stage.find_element(By.CSS_SELECTOR, ".pf-c-button").click()
