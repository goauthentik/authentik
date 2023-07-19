"""Test recovery flow"""
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import User
from authentik.core.tests.utils import create_test_admin_user
from authentik.flows.models import Flow
from authentik.lib.config import CONFIG
from authentik.lib.generators import generate_id
from authentik.stages.identification.models import IdentificationStage
from tests.e2e.utils import SeleniumTestCase, retry


class TestFlowsRecovery(SeleniumTestCase):
    """Test Recovery flow"""

    def initial_stages(self, user: User):
        """Fill out initial stages"""
        # Identification stage, click recovery
        flow_executor = self.get_shadow_root("ak-flow-executor")
        identification_stage = self.get_shadow_root("ak-stage-identification", flow_executor)
        wait = WebDriverWait(identification_stage, self.wait_timeout)

        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "#recovery")))
        identification_stage.find_element(By.CSS_SELECTOR, "#recovery").click()

        # First prompt stage
        flow_executor = self.get_shadow_root("ak-flow-executor")
        identification_stage = self.get_shadow_root("ak-stage-identification", flow_executor)
        wait = WebDriverWait(identification_stage, self.wait_timeout)

        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "input[name=uidField]")))
        identification_stage.find_element(By.CSS_SELECTOR, "input[name=uidField]").send_keys(
            user.username
        )
        identification_stage.find_element(By.CSS_SELECTOR, ".pf-c-button").click()

    @retry()
    @apply_blueprint(
        "default/flow-default-authentication-flow.yaml",
        "default/flow-default-invalidation-flow.yaml",
    )
    @apply_blueprint(
        "example/flows-recovery-email-verification.yaml",
    )
    @CONFIG.patch("email.port", 1025)
    def test_recover_email(self):
        """Test recovery with Email verification"""
        # Attach recovery flow to identification stage
        ident_stage: IdentificationStage = IdentificationStage.objects.get(
            name="default-authentication-identification"
        )
        ident_stage.recovery_flow = Flow.objects.filter(slug="default-recovery-flow").first()
        ident_stage.save()

        user = create_test_admin_user()

        self.driver.get(self.live_server_url)
        self.initial_stages(user)

        # Email stage
        flow_executor = self.get_shadow_root("ak-flow-executor")
        email_stage = self.get_shadow_root("ak-stage-email", flow_executor)

        wait = WebDriverWait(email_stage, self.wait_timeout)

        # Wait for the success message so we know the email is sent
        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, ".pf-c-form p")))

        # Open mailpit
        self.driver.get("http://localhost:8025")

        # Click on first message
        self.wait.until(ec.presence_of_element_located((By.CLASS_NAME, "message")))
        self.driver.find_element(By.CLASS_NAME, "message").click()
        self.driver.switch_to.frame(self.driver.find_element(By.ID, "preview-html"))
        self.driver.find_element(By.ID, "confirm").click()
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

        sleep(2)
        # We can now enter the new password
        flow_executor = self.get_shadow_root("ak-flow-executor")
        prompt_stage = self.get_shadow_root("ak-stage-prompt", flow_executor)
        wait = WebDriverWait(prompt_stage, self.wait_timeout)

        new_password = generate_id()

        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "input[name=password]")))
        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=password]").send_keys(new_password)
        prompt_stage.find_element(By.CSS_SELECTOR, "input[name=password_repeat]").send_keys(
            new_password
        )
        prompt_stage.find_element(By.CSS_SELECTOR, ".pf-c-button").click()

        # We're now logged in
        wait = WebDriverWait(self.get_shadow_root("ak-interface-user"), self.wait_timeout)

        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, ".pf-c-page__header")))
        self.driver.get(self.if_user_url("/settings"))

        self.assert_user(user)
        user.refresh_from_db()
        self.assertTrue(user.check_password(new_password))
