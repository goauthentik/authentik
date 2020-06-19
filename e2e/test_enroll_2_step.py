"""Test 2-step enroll flow"""
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from e2e.utils import apply_default_data
from passbook.flows.models import Flow, FlowDesignation, FlowStageBinding
from passbook.policies.expression.models import ExpressionPolicy
from passbook.policies.models import PolicyBinding
from passbook.stages.identification.models import IdentificationStage
from passbook.stages.prompt.models import FieldTypes, Prompt, PromptStage
from passbook.stages.user_login.models import UserLoginStage
from passbook.stages.user_write.models import UserWriteStage


class TestEnroll2Step(StaticLiveServerTestCase):
    """Test 2-step enroll flow"""

    def setUp(self):
        self.driver = webdriver.Remote(
            command_executor="http://localhost:4444/wd/hub",
            desired_capabilities=DesiredCapabilities.CHROME,
        )
        self.driver.implicitly_wait(5)
        apply_default_data()

    def tearDown(self):
        super().tearDown()
        self.driver.quit()

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

        FlowStageBinding.objects.create(flow=flow, stage=first_stage, order=0)
        FlowStageBinding.objects.create(flow=flow, stage=second_stage, order=1)
        FlowStageBinding.objects.create(flow=flow, stage=user_write, order=2)
        FlowStageBinding.objects.create(flow=flow, stage=user_login, order=3)
        self.driver.get(self.live_server_url)
        self.driver.find_element(By.CSS_SELECTOR, "[role=enroll]").click()
        self.driver.find_element(By.ID, "id_username").send_keys("foo")
        self.driver.find_element(By.ID, "id_password").send_keys("pbadmin")
        self.driver.find_element(By.ID, "id_password_repeat").send_keys("pbadmin")
        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-button").click()
        self.driver.find_element(By.ID, "id_name").send_keys("some name")
        self.driver.find_element(By.ID, "id_email").send_keys("foo@bar.baz")
        self.driver.find_element(By.CSS_SELECTOR, ".pf-c-button").click()
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
