"""Test Enroll flow"""

from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import User
from authentik.flows.models import Flow
from authentik.lib.config import CONFIG
from authentik.lib.generators import generate_id
from authentik.stages.identification.models import IdentificationStage
from tests.e2e.utils import SeleniumTestCase, retry


class TestFlowsEnroll(SeleniumTestCase):
    """Test Enroll flow"""

    def setUp(self):
        super().setUp()
        self.username = generate_id()

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
        sleep(2)

        user = User.objects.get(username=self.username)
        self.assertEqual(user.username, self.username)
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
    @CONFIG.patch("email.port", 1025)
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

        flow_executor = self.get_shadow_root("ak-flow-executor")
        consent_stage = self.get_shadow_root("ak-stage-consent", flow_executor)
        consent_stage.find_element(
            By.CSS_SELECTOR,
            "[type=submit]",
        ).click()

        self.wait_for_url(self.if_user_url())

        self.assert_user(User.objects.get(username=self.username))

    def initial_stages(self):
        """Fill out initial stages"""
        # Identification stage, click enroll
        flow_executor = self.get_shadow_root("ak-flow-executor")
        identification_stage = self.get_shadow_root("ak-stage-identification", flow_executor)
        wait = WebDriverWait(identification_stage, self.wait_timeout)

        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "a[name='enroll']")))
        identification_stage.find_element(By.CSS_SELECTOR, "a[name='enroll']").click()

        # First prompt stage
        flow_executor = self.get_shadow_root("ak-flow-executor")
        prompt_stage = self.get_shadow_root("ak-stage-prompt", flow_executor)
        wait = WebDriverWait(prompt_stage, self.wait_timeout)

        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "input[name=username]")))
        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=username]").send_keys(self.username)
        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=password]").send_keys(
            self.user.username
        )
        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=password_repeat]").send_keys(
            self.user.username
        )
        prompt_stage.find_element(By.CSS_SELECTOR, ".pf-c-button").click()

        # Second prompt stage
        sleep(1)
        flow_executor = self.get_shadow_root("ak-flow-executor")
        prompt_stage = self.get_shadow_root("ak-stage-prompt", flow_executor)
        wait = WebDriverWait(prompt_stage, self.wait_timeout)

        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "input[name=name]")))
        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=name]").send_keys("some name")
        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=email]").send_keys("foo@bar.baz")
        prompt_stage.find_element(By.CSS_SELECTOR, ".pf-c-button").click()

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "example/flows-enrollment-email-verification.yaml",
    )
    @CONFIG.patch("email.port", 1025)
    def test_enroll_email_pretend_email_scanner(self):
        """Test enroll with Email verification. Open the email link twice to pretend we have an
        email scanner that clicks on links"""
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
        confirmation_link = self.driver.find_element(By.ID, "confirm").get_attribute("href")

        main_tab = self.driver.current_window_handle

        self.driver.switch_to.new_window("tab")
        confirm_tab = self.driver.current_window_handle

        # On the new tab, check that we have the confirmation screen
        self.driver.get(confirmation_link)
        self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "ak-flow-executor")))

        flow_executor = self.get_shadow_root("ak-flow-executor")
        consent_stage = self.get_shadow_root("ak-stage-consent", flow_executor)

        self.assertEqual(
            "Continue to confirm this email address.",
            consent_stage.find_element(By.CSS_SELECTOR, "[data-test-id='stage-heading']").text,
        )

        # Back on the main tab, confirm
        self.driver.switch_to.window(main_tab)
        self.driver.get(confirmation_link)

        flow_executor = self.get_shadow_root("ak-flow-executor")
        consent_stage = self.get_shadow_root("ak-stage-consent", flow_executor)
        consent_stage.find_element(
            By.CSS_SELECTOR,
            "[type=submit]",
        ).click()

        self.wait_for_url(self.if_user_url())
        sleep(2)

        self.assert_user(User.objects.get(username=self.username))

        self.driver.switch_to.window(confirm_tab)
        self.driver.refresh()
        flow_executor = self.get_shadow_root("ak-flow-executor")
        wait = WebDriverWait(flow_executor, self.wait_timeout)
        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "ak-stage-access-denied")))
