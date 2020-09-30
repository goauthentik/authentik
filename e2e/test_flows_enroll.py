"""Test Enroll flow"""
from sys import platform
from typing import Any, Dict, Optional
from unittest.case import skipUnless

from django.test import override_settings
from docker.types import Healthcheck
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

from e2e.utils import USER, SeleniumTestCase
from passbook.flows.models import Flow, FlowDesignation, FlowStageBinding
from passbook.stages.email.models import EmailStage, EmailTemplates
from passbook.stages.identification.models import IdentificationStage
from passbook.stages.prompt.models import FieldTypes, Prompt, PromptStage
from passbook.stages.user_login.models import UserLoginStage
from passbook.stages.user_write.models import UserWriteStage


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestFlowsEnroll(SeleniumTestCase):
    """Test Enroll flow"""

    def get_container_specs(self) -> Optional[Dict[str, Any]]:
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
        first_stage = PromptStage.objects.create(name="prompt-stage-first")
        first_stage.fields.set([username_prompt, password, password_repeat])
        first_stage.save()
        second_stage = PromptStage.objects.create(name="prompt-stage-second")
        second_stage.fields.set([name_field, email])
        second_stage.save()
        user_write = UserWriteStage.objects.create(name="enroll-user-write")
        user_login = UserLoginStage.objects.create(name="enroll-user-login")

        flow = Flow.objects.create(
            name="default-enrollment-flow",
            slug="default-enrollment-flow",
            designation=FlowDesignation.ENROLLMENT,
        )

        # Attach enrollment flow to identification stage
        ident_stage: IdentificationStage = IdentificationStage.objects.first()
        ident_stage.enrollment_flow = flow
        ident_stage.save()

        FlowStageBinding.objects.create(target=flow, stage=first_stage, order=0)
        FlowStageBinding.objects.create(target=flow, stage=second_stage, order=1)
        FlowStageBinding.objects.create(target=flow, stage=user_write, order=2)
        FlowStageBinding.objects.create(target=flow, stage=user_login, order=3)

        self.driver.get(self.live_server_url)
        self.wait.until(
            ec.presence_of_element_located((By.CSS_SELECTOR, "[role=enroll]"))
        )
        self.driver.find_element(By.CSS_SELECTOR, "[role=enroll]").click()

        self.wait.until(ec.presence_of_element_located((By.ID, "id_username")))
        self.driver.find_element(By.ID, "id_username").send_keys("foo")
        self.driver.find_element(By.ID, "id_password").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_password_repeat").send_keys(USER().username)
        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-button").click()
        self.driver.find_element(By.ID, "id_name").send_keys("some name")
        self.driver.find_element(By.ID, "id_email").send_keys("foo@bar.baz")
        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-button").click()

        self.wait.until(ec.presence_of_element_located((By.LINK_TEXT, "foo")))
        self.driver.find_element(By.LINK_TEXT, "foo").click()

        self.wait_for_url(self.url("passbook_core:user-settings"))
        self.assertEqual(
            self.driver.find_element(By.ID, "user-settings").text,
            "foo",
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_username").get_attribute("value"), "foo"
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_name").get_attribute("value"),
            "some name",
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_email").get_attribute("value"),
            "foo@bar.baz",
        )

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend")
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
        first_stage = PromptStage.objects.create(name="prompt-stage-first")
        first_stage.fields.set([username_prompt, password, password_repeat])
        first_stage.save()
        second_stage = PromptStage.objects.create(name="prompt-stage-second")
        second_stage.fields.set([name_field, email])
        second_stage.save()
        email_stage = EmailStage.objects.create(
            name="enroll-email",
            host="localhost",
            port=1025,
            template=EmailTemplates.ACCOUNT_CONFIRM,
        )
        user_write = UserWriteStage.objects.create(name="enroll-user-write")
        user_login = UserLoginStage.objects.create(name="enroll-user-login")

        flow = Flow.objects.create(
            name="default-enrollment-flow",
            slug="default-enrollment-flow",
            designation=FlowDesignation.ENROLLMENT,
        )

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
        self.driver.find_element(By.CSS_SELECTOR, "[role=enroll]").click()
        self.driver.find_element(By.ID, "id_username").send_keys("foo")
        self.driver.find_element(By.ID, "id_password").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_password_repeat").send_keys(USER().username)
        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-button").click()
        self.driver.find_element(By.ID, "id_name").send_keys("some name")
        self.driver.find_element(By.ID, "id_email").send_keys("foo@bar.baz")
        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-button").click()
        # Wait for the success message so we know the email is sent
        self.wait.until(
            ec.presence_of_element_located((By.CSS_SELECTOR, ".pf-c-form > p"))
        )

        # Open Mailhog
        self.driver.get("http://localhost:8025")

        # Click on first message
        self.wait.until(
            ec.presence_of_element_located((By.CLASS_NAME, "msglist-message"))
        )
        self.driver.find_element(By.CLASS_NAME, "msglist-message").click()
        self.driver.switch_to.frame(self.driver.find_element(By.CLASS_NAME, "tab-pane"))
        self.driver.find_element(By.ID, "confirm").click()
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

        # We're now logged in
        self.wait.until(ec.presence_of_element_located((By.ID, "user-settings")))
        self.driver.find_element(By.ID, "user-settings").click()

        self.assertEqual(
            self.driver.find_element(By.ID, "user-settings").text,
            "foo",
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_username").get_attribute("value"), "foo"
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_name").get_attribute("value"),
            "some name",
        )
        self.assertEqual(
            self.driver.find_element(By.ID, "id_email").get_attribute("value"),
            "foo@bar.baz",
        )
