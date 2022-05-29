"""Test Enroll flow"""
from sys import platform
from time import sleep
from typing import Any, Optional
from unittest.case import skipUnless

from docker.types import Healthcheck
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from authentik.core.models import User
from authentik.core.tests.utils import create_test_flow
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.lib.generators import generate_id
from authentik.stages.email.models import EmailStage, EmailTemplates
from authentik.stages.identification.models import IdentificationStage
from authentik.stages.prompt.models import FieldTypes, Prompt, PromptStage
from authentik.stages.user_login.models import UserLoginStage
from authentik.stages.user_write.models import UserWriteStage
from tests.e2e.utils import SeleniumTestCase, apply_migration, retry


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestFlowsEnroll(SeleniumTestCase):
    """Test Enroll flow"""

    def get_container_specs(self) -> Optional[dict[str, Any]]:
        return {
            "image": "mailhog/mailhog:v1.0.1",
            "detach": True,
            "network_mode": "host",
            "auto_remove": True,
            "healthcheck": Healthcheck(
                test=["CMD", "wget", "--spider", "http://localhost:8025"],
                interval=5 * 100 * 1000000,
                start_period=1 * 100 * 1000000,
            ),
        }

    @retry()
    @apply_migration("authentik_flows", "0008_default_flows")
    @apply_migration("authentik_flows", "0011_flow_title")
    def test_enroll_2_step(self):
        """Test 2-step enroll flow"""
        # First stage fields
        username_prompt = Prompt.objects.create(
            field_key="username", label="Username", order=0, type=FieldTypes.TEXT
        )
        password = Prompt.objects.create(
            field_key="password", label="Password", order=1, type=FieldTypes.PASSWORD
        )
        password_repeat = Prompt.objects.create(
            field_key="password_repeat",
            label="Password (repeat)",
            order=2,
            type=FieldTypes.PASSWORD,
        )

        # Second stage fields
        name_field = Prompt.objects.create(
            field_key="name", label="Name", order=0, type=FieldTypes.TEXT
        )
        email = Prompt.objects.create(
            field_key="email", label="E-Mail", order=1, type=FieldTypes.EMAIL
        )

        # Stages
        first_stage = PromptStage.objects.create(name=generate_id())
        first_stage.fields.set([username_prompt, password, password_repeat])
        first_stage.save()
        second_stage = PromptStage.objects.create(name=generate_id())
        second_stage.fields.set([name_field, email])
        second_stage.save()
        user_write = UserWriteStage.objects.create(name=generate_id())
        user_login = UserLoginStage.objects.create(name=generate_id())

        flow = create_test_flow(FlowDesignation.ENROLLMENT)

        # Attach enrollment flow to identification stage
        ident_stage: IdentificationStage = IdentificationStage.objects.first()
        ident_stage.enrollment_flow = flow
        ident_stage.save()

        FlowStageBinding.objects.create(target=flow, stage=first_stage, order=0)
        FlowStageBinding.objects.create(target=flow, stage=second_stage, order=1)
        FlowStageBinding.objects.create(target=flow, stage=user_write, order=2)
        FlowStageBinding.objects.create(target=flow, stage=user_login, order=3)

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
    @apply_migration("authentik_flows", "0008_default_flows")
    @apply_migration("authentik_flows", "0011_flow_title")
    def test_enroll_email(self):
        """Test enroll with Email verification"""
        # First stage fields
        username_prompt = Prompt.objects.create(
            field_key="username", label="Username", order=0, type=FieldTypes.TEXT
        )
        password = Prompt.objects.create(
            field_key="password", label="Password", order=1, type=FieldTypes.PASSWORD
        )
        password_repeat = Prompt.objects.create(
            field_key="password_repeat",
            label="Password (repeat)",
            order=2,
            type=FieldTypes.PASSWORD,
        )

        # Second stage fields
        name_field = Prompt.objects.create(
            field_key="name", label="Name", order=0, type=FieldTypes.TEXT
        )
        email = Prompt.objects.create(
            field_key="email", label="E-Mail", order=1, type=FieldTypes.EMAIL
        )

        # Stages
        first_stage = PromptStage.objects.create(name=generate_id())
        first_stage.fields.set([username_prompt, password, password_repeat])
        first_stage.save()
        second_stage = PromptStage.objects.create(name=generate_id())
        second_stage.fields.set([name_field, email])
        second_stage.save()
        email_stage = EmailStage.objects.create(
            name=generate_id(),
            host="localhost",
            port=1025,
            template=EmailTemplates.ACCOUNT_CONFIRM,
        )
        user_write = UserWriteStage.objects.create(name=generate_id())
        user_login = UserLoginStage.objects.create(name=generate_id())

        flow = create_test_flow(FlowDesignation.ENROLLMENT)

        # Attach enrollment flow to identification stage
        ident_stage: IdentificationStage = IdentificationStage.objects.first()
        ident_stage.enrollment_flow = flow
        ident_stage.save()

        FlowStageBinding.objects.create(target=flow, stage=first_stage, order=0)
        FlowStageBinding.objects.create(target=flow, stage=second_stage, order=1)
        FlowStageBinding.objects.create(target=flow, stage=user_write, order=2)
        FlowStageBinding.objects.create(target=flow, stage=email_stage, order=3)
        FlowStageBinding.objects.create(target=flow, stage=user_login, order=4)

        self.driver.get(self.live_server_url)
        self.initial_stages()

        # Email stage
        flow_executor = self.get_shadow_root("ak-flow-executor")
        email_stage = self.get_shadow_root("ak-stage-email", flow_executor)

        wait = WebDriverWait(email_stage, self.wait_timeout)

        # Wait for the success message so we know the email is sent
        wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, ".pf-c-form p")))

        # Open Mailhog
        self.driver.get("http://localhost:8025")

        # Click on first message
        self.wait.until(ec.presence_of_element_located((By.CLASS_NAME, "msglist-message")))
        self.driver.find_element(By.CLASS_NAME, "msglist-message").click()
        self.driver.switch_to.frame(self.driver.find_element(By.CLASS_NAME, "tab-pane"))
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
