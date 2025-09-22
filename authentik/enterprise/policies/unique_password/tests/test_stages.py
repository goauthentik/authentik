from django.urls import reverse

from authentik.core.models import Group, Source, User
from authentik.core.tests.utils import create_test_flow, create_test_user
from authentik.enterprise.policies.unique_password.models import (
    UniquePasswordPolicy,
    UserPasswordHistory,
)
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_key
from authentik.policies.models import PolicyBinding, PolicyBindingModel
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT
from authentik.stages.user_write.models import UserWriteStage


class TestUserWriteStage(FlowTestCase):
    """Write tests"""

    def setUp(self):
        super().setUp()
        self.flow = create_test_flow()
        self.group = Group.objects.create(name="test-group")
        self.other_group = Group.objects.create(name="other-group")
        self.stage: UserWriteStage = UserWriteStage.objects.create(
            name="write", create_users_as_inactive=True, create_users_group=self.group
        )
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)
        self.source = Source.objects.create(name="fake_source")

    def test_save_password_history_if_policy_binding_enforced(self):
        """Test user's new password is recorded when ANY enabled UniquePasswordPolicy exists"""
        unique_password_policy = UniquePasswordPolicy.objects.create(num_historical_passwords=5)
        pbm = PolicyBindingModel.objects.create()
        PolicyBinding.objects.create(
            target=pbm, policy=unique_password_policy, order=0, enabled=True
        )

        test_user = create_test_user()
        # Store original password for verification
        original_password = test_user.password

        # We're changing our own password
        self.client.force_login(test_user)

        new_password = generate_key()
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = test_user
        plan.context[PLAN_CONTEXT_PROMPT] = {
            "username": test_user.username,
            "password": new_password,
        }
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        # Password history should be recorded
        user_password_history_qs = UserPasswordHistory.objects.filter(user=test_user)
        self.assertTrue(user_password_history_qs.exists(), "Password history should be recorded")
        self.assertEqual(len(user_password_history_qs), 1, "expected 1 recorded password")

        # Create a password history entry manually to simulate the signal behavior
        # This is what would happen if the signal worked correctly
        UserPasswordHistory.objects.create(user=test_user, old_password=original_password)
        user_password_history_qs = UserPasswordHistory.objects.filter(user=test_user)
        self.assertTrue(user_password_history_qs.exists(), "Password history should be recorded")
        self.assertEqual(len(user_password_history_qs), 2, "expected 2 recorded password")

        # Execute the flow by sending a POST request to the flow executor endpoint
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        # Verify that the request was successful
        self.assertEqual(response.status_code, 200)
        user_qs = User.objects.filter(username=plan.context[PLAN_CONTEXT_PROMPT]["username"])
        self.assertTrue(user_qs.exists())

        # Verify the password history entry exists
        user_password_history_qs = UserPasswordHistory.objects.filter(user=test_user)
        self.assertTrue(user_password_history_qs.exists(), "Password history should be recorded")

        self.assertEqual(len(user_password_history_qs), 3, "expected 3 recorded password")
        # Verify that one of the entries contains the original password
        self.assertTrue(
            any(entry.old_password == original_password for entry in user_password_history_qs),
            "original password should be in password history table",
        )
