"""Prompt tests"""
from unittest.mock import MagicMock, patch

from django.test import RequestFactory
from django.urls import reverse
from rest_framework.exceptions import ErrorDetail, ValidationError

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowStageBinding
from authentik.flows.planner import FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.policies.expression.models import ExpressionPolicy
from authentik.stages.prompt.models import FieldTypes, InlineFileField, Prompt, PromptStage
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT, PromptChallengeResponse


class TestPromptStage(FlowTestCase):
    """Prompt tests"""

    def setUp(self):
        super().setUp()
        self.user = create_test_admin_user()
        self.factory = RequestFactory()
        self.flow = create_test_flow()
        username_prompt = Prompt.objects.create(
            field_key="username_prompt",
            label="USERNAME_LABEL",
            type=FieldTypes.USERNAME,
            required=True,
            placeholder="USERNAME_PLACEHOLDER",
        )
        text_prompt = Prompt.objects.create(
            field_key="text_prompt",
            label="TEXT_LABEL",
            type=FieldTypes.TEXT,
            required=True,
            placeholder="TEXT_PLACEHOLDER",
        )
        email_prompt = Prompt.objects.create(
            field_key="email_prompt",
            label="EMAIL_LABEL",
            type=FieldTypes.EMAIL,
            required=True,
            placeholder="EMAIL_PLACEHOLDER",
        )
        password_prompt = Prompt.objects.create(
            field_key="password_prompt",
            label="PASSWORD_LABEL",
            type=FieldTypes.PASSWORD,
            required=True,
            placeholder="PASSWORD_PLACEHOLDER",
        )
        password2_prompt = Prompt.objects.create(
            field_key="password2_prompt",
            label="PASSWORD_LABEL",
            type=FieldTypes.PASSWORD,
            required=True,
            placeholder="PASSWORD_PLACEHOLDER",
        )
        number_prompt = Prompt.objects.create(
            field_key="number_prompt",
            label="NUMBER_LABEL",
            type=FieldTypes.NUMBER,
            required=True,
            placeholder="NUMBER_PLACEHOLDER",
        )
        hidden_prompt = Prompt.objects.create(
            field_key="hidden_prompt",
            type=FieldTypes.HIDDEN,
            required=True,
            placeholder="HIDDEN_PLACEHOLDER",
        )
        static_prompt = Prompt.objects.create(
            field_key="static_prompt",
            type=FieldTypes.STATIC,
            required=True,
            placeholder="static",
        )
        self.stage = PromptStage.objects.create(name="prompt-stage")
        self.stage.fields.set(
            [
                username_prompt,
                text_prompt,
                email_prompt,
                password_prompt,
                password2_prompt,
                number_prompt,
                hidden_prompt,
                static_prompt,
            ]
        )

        self.prompt_data = {
            username_prompt.field_key: "test-username",
            text_prompt.field_key: "test-input",
            email_prompt.field_key: "test@test.test",
            password_prompt.field_key: "test",
            password2_prompt.field_key: "test",
            number_prompt.field_key: 3,
            hidden_prompt.field_key: hidden_prompt.placeholder,
            static_prompt.field_key: static_prompt.placeholder,
        }

        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    def test_inline_file_field(self):
        """test InlineFileField"""
        with self.assertRaises(ValidationError):
            InlineFileField().to_internal_value("foo")
        with self.assertRaises(ValidationError):
            InlineFileField().to_internal_value("data:foo/bar;foo,qwer")
        self.assertEqual(
            InlineFileField().to_internal_value("data:mine/type;base64,Zm9v"),
            "data:mine/type;base64,Zm9v",
        )
        self.assertEqual(
            InlineFileField().to_internal_value("data:mine/type;base64,Zm9vqwer"),
            "data:mine/type;base64,Zm9vqwer",
        )

    def test_render(self):
        """Test render of form, check if all prompts are rendered correctly"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        self.assertEqual(response.status_code, 200)
        for prompt in self.stage.fields.all():
            self.assertIn(prompt.field_key, response.content.decode())
            self.assertIn(prompt.label, response.content.decode())
            self.assertIn(prompt.placeholder, response.content.decode())

    def test_valid_challenge_with_policy(self) -> PromptChallengeResponse:
        """Test challenge_response validation"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        expr = (
            "return request.context['prompt_data']['password_prompt'] "
            "== request.context['prompt_data']['password2_prompt']"
        )
        expr_policy = ExpressionPolicy.objects.create(name="validate-form", expression=expr)
        self.stage.validation_policies.set([expr_policy])
        self.stage.save()
        challenge_response = PromptChallengeResponse(
            None, stage=self.stage, plan=plan, data=self.prompt_data
        )
        self.assertEqual(challenge_response.is_valid(), True)
        return challenge_response

    def test_invalid_challenge(self) -> PromptChallengeResponse:
        """Test challenge_response validation"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        expr = "False"
        expr_policy = ExpressionPolicy.objects.create(name="validate-form", expression=expr)
        self.stage.validation_policies.set([expr_policy])
        self.stage.save()
        challenge_response = PromptChallengeResponse(
            None, stage=self.stage, plan=plan, data=self.prompt_data
        )
        self.assertEqual(challenge_response.is_valid(), False)
        return challenge_response

    def test_valid_challenge_request(self):
        """Test a request with valid challenge_response data"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        challenge_response = self.test_valid_challenge_with_policy()

        with patch("authentik.flows.views.executor.FlowExecutorView.cancel", MagicMock()):
            response = self.client.post(
                reverse(
                    "authentik_api:flow-executor",
                    kwargs={"flow_slug": self.flow.slug},
                ),
                challenge_response.validated_data,
            )
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

        # Check that valid data has been saved
        session = self.client.session
        plan: FlowPlan = session[SESSION_KEY_PLAN]
        data = plan.context[PLAN_CONTEXT_PROMPT]
        for prompt in self.stage.fields.all():
            prompt: Prompt
            self.assertEqual(data[prompt.field_key], self.prompt_data[prompt.field_key])

    def test_invalid_password(self):
        """Test challenge_response validation"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        self.prompt_data["password2_prompt"] = "qwerqwerqr"
        challenge_response = PromptChallengeResponse(
            None, stage=self.stage, plan=plan, data=self.prompt_data
        )
        self.assertEqual(challenge_response.is_valid(), False)
        self.assertEqual(
            challenge_response.errors,
            {"non_field_errors": [ErrorDetail(string="Passwords don't match.", code="invalid")]},
        )

    def test_invalid_username(self):
        """Test challenge_response validation"""
        user = create_test_admin_user()
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        self.prompt_data["username_prompt"] = user.username
        challenge_response = PromptChallengeResponse(
            None, stage=self.stage, plan=plan, data=self.prompt_data
        )
        self.assertEqual(challenge_response.is_valid(), False)
        self.assertEqual(
            challenge_response.errors,
            {"username_prompt": [ErrorDetail(string="Username is already taken.", code="invalid")]},
        )

    def test_static_hidden_overwrite(self):
        """Test that static and hidden fields ignore any value sent to them"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PROMPT] = {"hidden_prompt": "hidden"}
        self.prompt_data["hidden_prompt"] = "foo"
        self.prompt_data["static_prompt"] = "foo"
        challenge_response = PromptChallengeResponse(
            None, stage=self.stage, plan=plan, data=self.prompt_data
        )
        self.assertEqual(challenge_response.is_valid(), True)
        self.assertNotEqual(challenge_response.validated_data["hidden_prompt"], "foo")
        self.assertEqual(challenge_response.validated_data["hidden_prompt"], "hidden")
        self.assertNotEqual(challenge_response.validated_data["static_prompt"], "foo")

    def test_prompt_placeholder(self):
        """Test placeholder and expression"""
        context = {
            "foo": generate_id(),
        }
        prompt: Prompt = Prompt(
            field_key="text_prompt_expression",
            label="TEXT_LABEL",
            type=FieldTypes.TEXT,
            placeholder="return prompt_context['foo']",
            placeholder_expression=True,
        )
        self.assertEqual(
            prompt.get_placeholder(context, self.user, self.factory.get("/")), context["foo"]
        )
        context["text_prompt_expression"] = generate_id()
        self.assertEqual(
            prompt.get_placeholder(context, self.user, self.factory.get("/")),
            context["text_prompt_expression"],
        )
        self.assertNotEqual(
            prompt.get_placeholder(context, self.user, self.factory.get("/")), context["foo"]
        )

    def test_prompt_placeholder_error(self):
        """Test placeholder and expression"""
        context = {}
        prompt: Prompt = Prompt(
            field_key="text_prompt_expression",
            label="TEXT_LABEL",
            type=FieldTypes.TEXT,
            placeholder="something invalid dunno",
            placeholder_expression=True,
        )
        self.assertEqual(
            prompt.get_placeholder(context, self.user, self.factory.get("/")),
            "something invalid dunno",
        )

    def test_prompt_placeholder_disabled(self):
        """Test placeholder and expression"""
        context = {}
        prompt: Prompt = Prompt(
            field_key="text_prompt_expression",
            label="TEXT_LABEL",
            type=FieldTypes.TEXT,
            placeholder="return prompt_context['foo']",
            placeholder_expression=False,
        )
        self.assertEqual(
            prompt.get_placeholder(context, self.user, self.factory.get("/")), prompt.placeholder
        )

    def test_invalid_save(self):
        """Ensure field can't be saved with invalid type"""
        prompt: Prompt = Prompt(
            field_key="text_prompt_expression",
            label="TEXT_LABEL",
            type="foo",
            placeholder="foo",
            placeholder_expression=False,
            sub_text="test",
            order=123,
        )
        with self.assertRaises(ValueError):
            prompt.save()


def field_type_tester_factory(field_type: FieldTypes, required: bool):
    """Test field for field_type"""

    def tester(self: TestPromptStage):
        prompt: Prompt = Prompt(
            field_key="text_prompt_expression",
            label="TEXT_LABEL",
            type=field_type,
            placeholder="foo",
            placeholder_expression=False,
            sub_text="test",
            order=123,
            required=required,
        )
        self.assertIsNotNone(prompt.field("foo"))

    return tester


for _required in (True, False):
    for _type in FieldTypes:
        test_name = f"test_field_type_{_type}"
        if _required:
            test_name += "_required"
        setattr(TestPromptStage, test_name, field_type_tester_factory(_type, _required))
