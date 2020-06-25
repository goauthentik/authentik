"""Test Enroll flow"""
from time import sleep

from django.test import override_settings
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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


class TestEnroll(SeleniumTestCase):
    """Test Enroll flow"""

    def setUp(self):
        super().setUp()
        self.container = self.setup_client()

    def setup_client(self) -> Container:
        """Setup test IdP container"""
        client: DockerClient = from_env()
        container = client.containers.run(
            image="mailhog/mailhog",
            detach=True,
            network_mode="host",
            auto_remove=True,
            healthcheck=Healthcheck(
                test=["CMD", "wget", "-s", "http://localhost:8025"],
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

    # pylint: disable=too-many-statements
    def setup_test_enroll_2_step(self):
        """Setup all required objects"""
        self.driver.find_element(By.ID, "id_uid_field").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_uid_field").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, "id_password").send_keys(USER().username)
        self.driver.find_element(By.ID, "id_password").send_keys(Keys.ENTER)
        self.driver.find_element(By.LINK_TEXT, "Administrate").click()
        self.driver.find_element(By.LINK_TEXT, "Prompts").click()

        # Create Password Prompt
        self.driver.find_element(By.LINK_TEXT, "Create").click()
        self.driver.find_element(By.ID, "id_field_key").send_keys("password")
        self.driver.find_element(By.ID, "id_label").send_keys("Password")
        dropdown = self.driver.find_element(By.ID, "id_type")
        dropdown.find_element(By.XPATH, "//option[. = 'Password']").click()
        self.driver.find_element(By.ID, "id_placeholder").send_keys("Password")
        self.driver.find_element(By.ID, "id_order").send_keys("1")
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        # Create Password Repeat Prompt
        self.driver.find_element(By.LINK_TEXT, "Create").click()
        self.driver.find_element(By.ID, "id_field_key").send_keys("password_repeat")
        self.driver.find_element(By.ID, "id_label").send_keys("Password (repeat)")
        dropdown = self.driver.find_element(By.ID, "id_type")
        dropdown.find_element(By.XPATH, "//option[. = 'Password']").click()
        self.driver.find_element(By.ID, "id_placeholder").send_keys("Password (repeat)")
        self.driver.find_element(By.ID, "id_order").send_keys("2")
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        # Create Name Prompt
        self.driver.find_element(By.LINK_TEXT, "Create").click()
        self.driver.find_element(By.ID, "id_field_key").send_keys("name")
        self.driver.find_element(By.ID, "id_label").send_keys("Name")
        dropdown = self.driver.find_element(By.ID, "id_type")
        dropdown.find_element(By.XPATH, "//option[. = 'Text']").click()
        self.driver.find_element(By.ID, "id_placeholder").send_keys("Name")
        self.driver.find_element(By.ID, "id_order").send_keys("0")
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        # Create Email Prompt
        self.driver.find_element(By.LINK_TEXT, "Create").click()
        self.driver.find_element(By.ID, "id_field_key").send_keys("email")
        self.driver.find_element(By.ID, "id_label").send_keys("Email")
        dropdown = self.driver.find_element(By.ID, "id_type")
        dropdown.find_element(By.XPATH, "//option[. = 'Email']").click()
        self.driver.find_element(By.ID, "id_placeholder").send_keys("Email")
        self.driver.find_element(By.ID, "id_order").send_keys("1")
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        self.driver.find_element(By.LINK_TEXT, "Stages").click()

        # Create first enroll prompt stage
        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-dropdown__toggle").click()
        self.driver.find_element(
            By.CSS_SELECTOR, "li:nth-child(9) > .pf-c-dropdown__menu-item > small"
        ).click()
        self.driver.find_element(By.ID, "id_name").send_keys(
            "enroll-prompt-stage-first"
        )
        dropdown = self.driver.find_element(By.ID, "id_fields")
        dropdown.find_element(
            By.XPATH, "//option[. = \"Prompt 'username' type=text\"]"
        ).click()
        dropdown.find_element(
            By.XPATH, "//option[. = \"Prompt 'password' type=password\"]"
        ).click()
        dropdown.find_element(
            By.XPATH, "//option[. = \"Prompt 'password_repeat' type=password\"]"
        ).click()
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        # Create second enroll prompt stage
        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-dropdown__toggle").click()
        self.driver.find_element(
            By.CSS_SELECTOR, "li:nth-child(9) > .pf-c-dropdown__menu-item"
        ).click()
        self.driver.find_element(By.ID, "id_name").send_keys(
            "enroll-prompt-stage-second"
        )
        dropdown = self.driver.find_element(By.ID, "id_fields")
        dropdown.find_element(
            By.XPATH, "//option[. = \"Prompt 'name' type=text\"]"
        ).click()
        dropdown.find_element(
            By.XPATH, "//option[. = \"Prompt 'email' type=email\"]"
        ).click()
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        # Create user write stage
        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-dropdown__toggle").click()
        self.driver.find_element(
            By.CSS_SELECTOR, "li:nth-child(13) > .pf-c-dropdown__menu-item"
        ).click()
        self.driver.find_element(By.ID, "id_name").send_keys("enroll-user-write")
        self.driver.find_element(By.ID, "id_name").send_keys(Keys.ENTER)
        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-dropdown__toggle").click()

        # Create user login stage
        self.driver.find_element(
            By.CSS_SELECTOR, "li:nth-child(11) > .pf-c-dropdown__menu-item"
        ).click()
        self.driver.find_element(By.ID, "id_name").send_keys("enroll-user-login")
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        self.driver.find_element(
            By.CSS_SELECTOR,
            ".pf-c-nav__item:nth-child(7) .pf-c-nav__item:nth-child(1) > .pf-c-nav__link",
        ).click()

        # Create password policy
        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-dropdown__toggle").click()
        self.driver.find_element(
            By.CSS_SELECTOR, "li:nth-child(2) > .pf-c-dropdown__menu-item > small"
        ).click()
        self.driver.find_element(By.ID, "id_name").send_keys(
            "policy-enrollment-password-equals"
        )
        self.wait.until(
            ec.presence_of_element_located((By.CSS_SELECTOR, ".CodeMirror-scroll"))
        )
        self.driver.find_element(By.CSS_SELECTOR, ".CodeMirror-scroll").click()
        self.driver.find_element(By.CSS_SELECTOR, ".CodeMirror textarea").send_keys(
            "return request.context['password'] == request.context['password_repeat']"
        )
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        # Create password policy binding
        self.driver.find_element(
            By.CSS_SELECTOR,
            ".pf-c-nav__item:nth-child(7) .pf-c-nav__item:nth-child(2) > .pf-c-nav__link",
        ).click()
        self.driver.find_element(By.LINK_TEXT, "Create").click()
        dropdown = self.driver.find_element(By.ID, "id_policy")
        dropdown.find_element(
            By.XPATH, '//option[. = "Policy policy-enrollment-password-equals"]'
        ).click()
        self.driver.find_element(By.ID, "id_target").click()
        dropdown = self.driver.find_element(By.ID, "id_target")
        dropdown.find_element(
            By.XPATH, '//option[. = "Prompt Stage enroll-prompt-stage-first"]'
        ).click()
        self.driver.find_element(By.ID, "id_order").send_keys("0")
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        # Create Flow
        self.driver.find_element(
            By.CSS_SELECTOR,
            ".pf-c-nav__item:nth-child(6) .pf-c-nav__item:nth-child(1) > .pf-c-nav__link",
        ).click()
        self.driver.find_element(By.LINK_TEXT, "Create").click()
        self.driver.find_element(By.ID, "id_name").send_keys("Welcome")
        self.driver.find_element(By.ID, "id_slug").clear()
        self.driver.find_element(By.ID, "id_slug").send_keys("default-enrollment-flow")
        dropdown = self.driver.find_element(By.ID, "id_designation")
        dropdown.find_element(By.XPATH, '//option[. = "Enrollment"]').click()
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        self.driver.find_element(By.LINK_TEXT, "Stages").click()

        # Edit identification stage
        self.driver.find_element(
            By.CSS_SELECTOR, "tr:nth-child(11) .pf-m-secondary"
        ).click()
        self.driver.find_element(
            By.CSS_SELECTOR,
            ".pf-c-form__group:nth-child(5) .pf-c-form__horizontal-group",
        ).click()
        self.driver.find_element(By.ID, "id_enrollment_flow").click()
        dropdown = self.driver.find_element(By.ID, "id_enrollment_flow")
        dropdown.find_element(
            By.XPATH, '//option[. = "Flow Welcome (default-enrollment-flow)"]'
        ).click()
        self.driver.find_element(By.ID, "id_user_fields_add_all_link").click()
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        self.driver.find_element(By.LINK_TEXT, "Bindings").click()

        # Create Stage binding for first prompt stage
        self.driver.find_element(By.LINK_TEXT, "Create").click()
        self.driver.find_element(By.ID, "id_flow").click()
        dropdown = self.driver.find_element(By.ID, "id_flow")
        dropdown.find_element(
            By.XPATH, '//option[. = "Flow Welcome (default-enrollment-flow)"]'
        ).click()
        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-form").click()
        self.driver.find_element(By.ID, "id_stage").click()
        dropdown = self.driver.find_element(By.ID, "id_stage")
        dropdown.find_element(
            By.XPATH, '//option[. = "Stage enroll-prompt-stage-first"]'
        ).click()
        self.driver.find_element(By.ID, "id_order").click()
        self.driver.find_element(By.ID, "id_order").send_keys("0")
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        # Create Stage binding for second prompt stage
        self.driver.find_element(By.LINK_TEXT, "Create").click()
        self.driver.find_element(By.ID, "id_flow").click()
        dropdown = self.driver.find_element(By.ID, "id_flow")
        dropdown.find_element(
            By.XPATH, '//option[. = "Flow Welcome (default-enrollment-flow)"]'
        ).click()
        self.driver.find_element(By.ID, "id_stage").click()
        dropdown = self.driver.find_element(By.ID, "id_stage")
        dropdown.find_element(
            By.XPATH, '//option[. = "Stage enroll-prompt-stage-second"]'
        ).click()
        self.driver.find_element(By.ID, "id_order").click()
        self.driver.find_element(By.ID, "id_order").send_keys("1")
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        # Create Stage binding for user write stage
        self.driver.find_element(By.LINK_TEXT, "Create").click()
        self.driver.find_element(By.ID, "id_flow").click()
        dropdown = self.driver.find_element(By.ID, "id_flow")
        dropdown.find_element(
            By.XPATH, '//option[. = "Flow Welcome (default-enrollment-flow)"]'
        ).click()
        self.driver.find_element(By.ID, "id_stage").click()
        dropdown = self.driver.find_element(By.ID, "id_stage")
        dropdown.find_element(
            By.XPATH, '//option[. = "Stage enroll-user-write"]'
        ).click()
        self.driver.find_element(By.ID, "id_order").click()
        self.driver.find_element(By.ID, "id_order").send_keys("2")
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        # Create Stage binding for user login stage
        self.driver.find_element(By.LINK_TEXT, "Create").click()
        dropdown = self.driver.find_element(By.ID, "id_flow")
        dropdown.find_element(
            By.XPATH, '//option[. = "Flow Welcome (default-enrollment-flow)"]'
        ).click()
        dropdown = self.driver.find_element(By.ID, "id_stage")
        dropdown.find_element(
            By.XPATH, '//option[. = "Stage enroll-user-login"]'
        ).click()
        self.driver.find_element(By.ID, "id_order").send_keys("3")
        self.driver.find_element(
            By.CSS_SELECTOR, ".pf-c-form__actions > .pf-m-primary"
        ).click()

        self.driver.find_element(By.CSS_SELECTOR, "[aria-label=logout]").click()

    def test_enroll_2_step(self):
        """Test 2-step enroll flow"""
        self.driver.get(self.live_server_url)
        self.setup_test_enroll_2_step()
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

        FlowStageBinding.objects.create(flow=flow, stage=first_stage, order=0)
        FlowStageBinding.objects.create(flow=flow, stage=second_stage, order=1)
        FlowStageBinding.objects.create(flow=flow, stage=user_write, order=2)
        FlowStageBinding.objects.create(flow=flow, stage=email_stage, order=3)
        FlowStageBinding.objects.create(flow=flow, stage=user_login, order=4)

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
