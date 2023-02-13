"""policy engine tests"""
from django.core.cache import cache
from django.test import TestCase

from authentik.core.models import User
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.engine import PolicyEngine
from authentik.policies.exceptions import PolicyEngineException
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import Policy, PolicyBinding, PolicyBindingModel, PolicyEngineMode
from authentik.policies.tests.test_process import clear_policy_cache
from authentik.policies.types import CACHE_PREFIX


class TestPolicyEngine(TestCase):
    """PolicyEngine tests"""

    def setUp(self):
        clear_policy_cache()
        self.user = User.objects.create_user(username="policyuser")
        self.policy_false = DummyPolicy.objects.create(result=False, wait_min=0, wait_max=1)
        self.policy_true = DummyPolicy.objects.create(result=True, wait_min=0, wait_max=1)
        self.policy_wrong_type = Policy.objects.create(name="wrong_type")
        self.policy_raises = ExpressionPolicy.objects.create(name="raises", expression="{{ 0/0 }}")

    def test_engine_empty(self):
        """Ensure empty policy list passes"""
        pbm = PolicyBindingModel.objects.create()
        engine = PolicyEngine(pbm, self.user)
        result = engine.build().result
        self.assertEqual(result.passing, True)
        self.assertEqual(result.messages, ())

    def test_engine_simple(self):
        """Ensure simplest use-case"""
        pbm = PolicyBindingModel.objects.create()
        PolicyBinding.objects.create(target=pbm, policy=self.policy_true, order=0)
        engine = PolicyEngine(pbm, self.user)
        result = engine.build().result
        self.assertEqual(result.passing, True)
        self.assertEqual(result.messages, ("dummy",))

    def test_engine_mode_all(self):
        """Ensure all policies passes with AND mode (false and true -> false)"""
        pbm = PolicyBindingModel.objects.create(policy_engine_mode=PolicyEngineMode.MODE_ALL)
        PolicyBinding.objects.create(target=pbm, policy=self.policy_false, order=0)
        PolicyBinding.objects.create(target=pbm, policy=self.policy_true, order=1)
        engine = PolicyEngine(pbm, self.user)
        result = engine.build().result
        self.assertEqual(result.passing, False)
        self.assertEqual(
            result.messages,
            (
                "dummy",
                "dummy",
            ),
        )

    def test_engine_mode_any(self):
        """Ensure all policies passes with OR mode (false and true -> true)"""
        pbm = PolicyBindingModel.objects.create(policy_engine_mode=PolicyEngineMode.MODE_ANY)
        PolicyBinding.objects.create(target=pbm, policy=self.policy_false, order=0)
        PolicyBinding.objects.create(target=pbm, policy=self.policy_true, order=1)
        engine = PolicyEngine(pbm, self.user)
        result = engine.build().result
        self.assertEqual(result.passing, True)
        self.assertEqual(
            result.messages,
            (
                "dummy",
                "dummy",
            ),
        )

    def test_engine_negate(self):
        """Test negate flag"""
        pbm = PolicyBindingModel.objects.create()
        PolicyBinding.objects.create(target=pbm, policy=self.policy_true, negate=True, order=0)
        engine = PolicyEngine(pbm, self.user)
        result = engine.build().result
        self.assertEqual(result.passing, False)
        self.assertEqual(result.messages, ("dummy",))

    def test_engine_policy_error(self):
        """Test policy raising an error flag"""
        pbm = PolicyBindingModel.objects.create()
        PolicyBinding.objects.create(target=pbm, policy=self.policy_raises, order=0)
        engine = PolicyEngine(pbm, self.user)
        result = engine.build().result
        self.assertEqual(result.passing, False)
        self.assertEqual(result.messages, ("division by zero",))

    def test_engine_policy_type(self):
        """Test invalid policy type"""
        pbm = PolicyBindingModel.objects.create()
        PolicyBinding.objects.create(target=pbm, policy=self.policy_wrong_type, order=0)
        with self.assertRaises(PolicyEngineException):
            engine = PolicyEngine(pbm, self.user)
            engine.build()

    def test_engine_cache(self):
        """Ensure empty policy list passes"""
        pbm = PolicyBindingModel.objects.create()
        binding = PolicyBinding.objects.create(target=pbm, policy=self.policy_false, order=0)
        engine = PolicyEngine(pbm, self.user)
        self.assertEqual(len(cache.keys(f"{CACHE_PREFIX}{binding.policy_binding_uuid.hex}*")), 0)
        self.assertEqual(engine.build().passing, False)
        self.assertEqual(len(cache.keys(f"{CACHE_PREFIX}{binding.policy_binding_uuid.hex}*")), 1)
        self.assertEqual(engine.build().passing, False)
        self.assertEqual(len(cache.keys(f"{CACHE_PREFIX}{binding.policy_binding_uuid.hex}*")), 1)
