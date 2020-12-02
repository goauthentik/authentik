"""Prompt tests"""
from unittest.mock import MagicMock, patch

from django.shortcuts import reverse
from django.test import Client, TestCase
from django.utils.encoding import force_str

from authentik.core.models import User
from authentik.flows.markers import StageMarker
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.flows.planner import FlowPlan
from authentik.flows.views import SESSION_KEY_PLAN
from authentik.policies.expression.models import ExpressionPolicy
from authentik.stages.prompt.forms import PromptForm
from authentik.stages.prompt.models import FieldTypes, Prompt, PromptStage
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT


class TestPromptStage(TestCase):
    """Prompt tests"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create(username="unittest", email="test@beryju.org")
        self.client = Client()

        self.flow = Flow.objects.create(
            name="test-prompt",
            slug="test-prompt",
            designation=FlowDesignation.AUTHENTICATION,
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
        self.stage = PromptStage.objects.create(name="prompt-stage")
        self.stage.fields.set(
            [
                text_prompt,
                email_prompt,
                password_prompt,
                password2_prompt,
                number_prompt,
                hidden_prompt,
            ]
        )
        self.stage.save()

        self.prompt_data = {
            text_prompt.field_key: "test-input",
            email_prompt.field_key: "test@test.test",
            password_prompt.field_key: "test",
            password2_prompt.field_key: "test",
            number_prompt.field_key: 3,
            hidden_prompt.field_key: hidden_prompt.placeholder,
        }

        FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)

    def test_render(self):
        """Test render of form, check if all prompts are rendered correctly"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse(
                "authentik_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            )
        )
        self.assertEqual(response.status_code, 200)
        for prompt in self.stage.fields.all():
            self.assertIn(prompt.field_key, force_str(response.content))
            self.assertIn(prompt.label, force_str(response.content))
            self.assertIn(prompt.placeholder, force_str(response.content))

    def test_valid_form_with_policy(self) -> PromptForm:
        """Test form validation"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        expr = "return request.context['password_prompt'] == request.context['password2_prompt']"
        expr_policy = ExpressionPolicy.objects.create(
            name="validate-form", expression=expr
        )
        self.stage.validation_policies.set([expr_policy])
        self.stage.save()
        form = PromptForm(stage=self.stage, plan=plan, data=self.prompt_data)
        self.assertEqual(form.is_valid(), True)
        return form

    def test_invalid_form(self) -> PromptForm:
        """Test form validation"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        expr = "False"
        expr_policy = ExpressionPolicy.objects.create(
            name="validate-form", expression=expr
        )
        self.stage.validation_policies.set([expr_policy])
        self.stage.save()
        form = PromptForm(stage=self.stage, plan=plan, data=self.prompt_data)
        self.assertEqual(form.is_valid(), False)
        return form

    def test_valid_form_request(self):
        """Test a request with valid form data"""
        plan = FlowPlan(
            flow_pk=self.flow.pk.hex, stages=[self.stage], markers=[StageMarker()]
        )
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        form = self.test_valid_form_with_policy()

        with patch("authentik.flows.views.FlowExecutorView.cancel", MagicMock()):
            response = self.client.post(
                reverse(
                    "authentik_flows:flow-executor",
                    kwargs={"flow_slug": self.flow.slug},
                ),
                form.cleaned_data,
            )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {"type": "redirect", "to": reverse("authentik_core:shell")},
        )

        # Check that valid data has been saved
        session = self.client.session
        plan: FlowPlan = session[SESSION_KEY_PLAN]
        data = plan.context[PLAN_CONTEXT_PROMPT]
        for prompt in self.stage.fields.all():
            prompt: Prompt
            self.assertEqual(data[prompt.field_key], self.prompt_data[prompt.field_key])
