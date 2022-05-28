"""Password flow tests"""
from django.urls.base import reverse

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.tests import FlowTestCase
from authentik.policies.password.models import PasswordPolicy
from authentik.stages.prompt.models import FieldTypes, Prompt, PromptStage


class TestPasswordPolicyFlow(FlowTestCase):
    """Test Password Policy"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)

        password_prompt = Prompt.objects.create(
            field_key="password",
            label="PASSWORD_LABEL",
            type=FieldTypes.PASSWORD,
            required=True,
            placeholder="PASSWORD_PLACEHOLDER",
        )

        self.policy = PasswordPolicy.objects.create(
            name="test_true",
            amount_uppercase=1,
            amount_lowercase=2,
            amount_symbols=3,
            length_min=3,
            error_message="test message",
        )
        stage = PromptStage.objects.create(name="prompt-stage")
        stage.validation_policies.set([self.policy])
        stage.fields.set(
            [
                password_prompt,
            ]
        )
        FlowStageBinding.objects.create(target=self.flow, stage=stage, order=2)

    def test_prompt_data(self):
        """Test policy attached to a prompt stage"""
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            {"password": "akadmin"},
        )
        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-prompt",
            fields=[
                {
                    "field_key": "password",
                    "label": "PASSWORD_LABEL",
                    "order": 0,
                    "placeholder": "PASSWORD_PLACEHOLDER",
                    "required": True,
                    "type": "password",
                    "sub_text": "",
                }
            ],
            response_errors={
                "non_field_errors": [{"code": "invalid", "string": self.policy.error_message}]
            },
        )
