"""Unique Password Policy flow tests"""

from django.contrib.auth.hashers import make_password
from django.urls.base import reverse

from authentik.core.tests.utils import create_test_flow, create_test_user
from authentik.crypto.generators import generate_id
from authentik.enterprise.policies.unique_password.models import (
    UniquePasswordPolicy,
    UserPasswordHistory,
)
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.tests import FlowTestCase
from authentik.stages.prompt.models import FieldTypes, Prompt, PromptStage


class TestUniquePasswordPolicyFlow(FlowTestCase):
    """Test Unique Password Policy in a flow"""

    REUSED_PASSWORD = "hunter1"  # nosec B105

    def setUp(self) -> None:
        self.user = create_test_user()
        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)

        password_prompt = Prompt.objects.create(
            name=generate_id(),
            field_key="password",
            label="PASSWORD_LABEL",
            type=FieldTypes.PASSWORD,
            required=True,
            placeholder="PASSWORD_PLACEHOLDER",
        )

        self.policy = UniquePasswordPolicy.objects.create(
            name="password_must_unique",
            password_field=password_prompt.field_key,
            num_historical_passwords=1,
        )
        stage = PromptStage.objects.create(name="prompt-stage")
        stage.validation_policies.set([self.policy])
        stage.fields.set(
            [
                password_prompt,
            ]
        )
        FlowStageBinding.objects.create(target=self.flow, stage=stage, order=2)

        # Seed the user's password history
        UserPasswordHistory.create_for_user(self.user, make_password(self.REUSED_PASSWORD))

    def test_prompt_data(self):
        """Test policy attached to a prompt stage"""
        # Test the policy directly
        from authentik.policies.types import PolicyRequest
        from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

        # Create a policy request with the reused password
        request = PolicyRequest(user=self.user)
        request.context[PLAN_CONTEXT_PROMPT] = {"password": self.REUSED_PASSWORD}

        # Test the policy directly
        result = self.policy.passes(request)

        # Verify that the policy fails (returns False) with the expected error message
        self.assertFalse(result.passing, "Policy should fail for reused password")
        self.assertEqual(
            result.messages[0],
            "This password has been used previously. Please choose a different one.",
            "Incorrect error message",
        )

        # API-based testing approach:

        self.client.force_login(self.user)

        # Send a POST request to the flow executor with the reused password
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            {"password": self.REUSED_PASSWORD},
        )
        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-prompt",
            fields=[
                {
                    "choices": None,
                    "field_key": "password",
                    "label": "PASSWORD_LABEL",
                    "order": 0,
                    "placeholder": "PASSWORD_PLACEHOLDER",
                    "initial_value": "",
                    "required": True,
                    "type": "password",
                    "sub_text": "",
                }
            ],
            response_errors={
                "non_field_errors": [
                    {
                        "code": "invalid",
                        "string": "This password has been used previously. "
                        "Please choose a different one.",
                    }
                ]
            },
        )
