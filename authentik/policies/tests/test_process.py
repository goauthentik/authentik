"""policy process tests"""
from django.core.cache import cache
from django.test import TestCase

from authentik.core.models import User
from authentik.events.models import Event, EventAction
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import Policy, PolicyBinding
from authentik.policies.process import PolicyProcess
from authentik.policies.types import PolicyRequest


def clear_policy_cache():
    """Ensure no policy-related keys are stil cached"""
    keys = cache.keys("policy_*")
    cache.delete(keys)


class TestPolicyProcess(TestCase):
    """Policy Process tests"""

    def setUp(self):
        clear_policy_cache()
        self.user = User.objects.create_user(username="policyuser")

    def test_invalid(self):
        """Test Process with invalid arguments"""
        policy = DummyPolicy.objects.create(result=True, wait_min=0, wait_max=1)
        binding = PolicyBinding(policy=policy)
        with self.assertRaises(ValueError):
            PolicyProcess(binding, None, None)  # type: ignore

    def test_true(self):
        """Test policy execution"""
        policy = DummyPolicy.objects.create(result=True, wait_min=0, wait_max=1)
        binding = PolicyBinding(policy=policy)

        request = PolicyRequest(self.user)
        response = PolicyProcess(binding, request, None).execute()
        self.assertEqual(response.passing, True)
        self.assertEqual(response.messages, ("dummy",))

    def test_false(self):
        """Test policy execution"""
        policy = DummyPolicy.objects.create(result=False, wait_min=0, wait_max=1)
        binding = PolicyBinding(policy=policy)

        request = PolicyRequest(self.user)
        response = PolicyProcess(binding, request, None).execute()
        self.assertEqual(response.passing, False)
        self.assertEqual(response.messages, ("dummy",))

    def test_negate(self):
        """Test policy execution"""
        policy = DummyPolicy.objects.create(result=False, wait_min=0, wait_max=1)
        binding = PolicyBinding(policy=policy, negate=True)

        request = PolicyRequest(self.user)
        response = PolicyProcess(binding, request, None).execute()
        self.assertEqual(response.passing, True)
        self.assertEqual(response.messages, ("dummy",))

    def test_exception(self):
        """Test policy execution"""
        policy = Policy.objects.create()
        binding = PolicyBinding(policy=policy)

        request = PolicyRequest(self.user)
        response = PolicyProcess(binding, request, None).execute()
        self.assertEqual(response.passing, False)

    def test_execution_logging(self):
        """Test policy execution creates event"""
        policy = DummyPolicy.objects.create(
            result=False, wait_min=0, wait_max=1, execution_logging=True
        )
        binding = PolicyBinding(policy=policy)

        request = PolicyRequest(self.user)
        response = PolicyProcess(binding, request, None).execute()
        self.assertEqual(response.passing, False)
        self.assertEqual(response.messages, ("dummy",))

        events = Event.objects.filter(
            action=EventAction.POLICY_EXECUTION,
        )
        self.assertTrue(events.exists())
        self.assertEqual(len(events), 1)
        event = events.first()
        self.assertEqual(event.context["result"]["passing"], False)
        self.assertEqual(event.context["result"]["messages"], ["dummy"])

    def test_raises(self):
        """Test policy that raises error"""
        policy_raises = ExpressionPolicy.objects.create(
            name="raises", expression="{{ 0/0 }}"
        )
        binding = PolicyBinding(policy=policy_raises)

        request = PolicyRequest(self.user)
        response = PolicyProcess(binding, request, None).execute()
        self.assertEqual(response.passing, False)
        self.assertEqual(response.messages, ("division by zero",))
        # self.assert
