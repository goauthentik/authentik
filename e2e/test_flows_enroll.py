"""Test Enroll flow"""
from time import sleep

from django.test import override_settings
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

from docker import DockerClient, from_env
from docker.models.containers import Container
from docker.types import Healthcheck
from e2e.utils import USER, SeleniumTestCase
from passbook.flows.models import Flow, FlowDesignation, FlowStageBinding
from passbook.policies.expression.models import ExpressionPolicy
from passbook.policies.models import PolicyBinding
from passbook.stages.email.models import EmailStage, EmailTemplates
from passbook.stages.identification.models import IdentificationStage
from passbook.stages.prompt.models import FieldTypes, Prompt, PromptStage
from passbook.stages.user_login.models import UserLoginStage
from passbook.stages.user_write.models import UserWriteStage


class TestFlowsEnroll(SeleniumTestCase):
    """Test Enroll flow"""

    def setUp(self):
        self.container = self.setup_client()
        super().setUp()

    def setup_client(self) -> Container:
        """Setup test IdP container"""
        client: DockerClient = from_env()
        container = client.containers.run(
            image="mailhog/mailhog:v.1.0.1",
            detach=True,
            network_mode="host",
            auto_remove=True,
            healthcheck=Healthcheck(
                test=["CMD", "wget", "--spider", "http://localhost:8025"],
                interval=5 * 100 * 1000000,
                start_period=1 * 100 * 1000000,
            ),
        )
        while True:
            container.reload()
            status = container.attrs.get("State", {}).get("Health", {}).get("Status")
            if status == "healthy":
                return container
            sleep(1)

    def tearDown(self):
        self.container.kill()
        super().tearDown()

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

        # Password checking policy
        password_policy = ExpressionPolicy.objects.create(
            name="policy-enrollment-password-equals",
            expression="return request.context['password'] == request.context['password_repeat']",
        )
        PolicyBinding.objects.create(
            target=first_stage, policy=password_policy, order=0
        )

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
            self.driver.find_element(By.XPATH, "//a[contains(@href, '/-/user/')]").text,
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

        # Password checking policy
        password_policy = ExpressionPolicy.objects.create(
            name="policy-enrollment-password-equals",
            expression="return request.context['password'] == request.context['password_repeat']",
        )
        PolicyBinding.objects.create(
            target=first_stage, policy=password_policy, order=0
        )

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
        sleep(3)

        # Open Mailhog
        self.driver.get("http://localhost:8025")

        # Click on first message
        self.driver.find_element(By.CLASS_NAME, "msglist-message").click()
        sleep(3)
        self.driver.switch_to.frame(self.driver.find_element(By.CLASS_NAME, "tab-pane"))
        self.driver.find_element(By.ID, "confirm").click()
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

        # We're now logged in
        sleep(3)
        self.wait.until(
            ec.presence_of_element_located(
                (By.XPATH, "//a[contains(@href, '/-/user/')]")
            )
        )
        self.driver.find_element(By.XPATH, "//a[contains(@href, '/-/user/')]").click()

        self.assertEqual(
            self.driver.find_element(By.XPATH, "//a[contains(@href, '/-/user/')]").text,
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
