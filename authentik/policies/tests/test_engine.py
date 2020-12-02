"""policy engine tests"""
from django.core.cache import cache
from django.test import TestCase

from authentik.core.models import User
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.engine import PolicyEngine
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import Policy, PolicyBinding, PolicyBindingModel


class TestPolicyEngine(TestCase):
    """PolicyEngine tests"""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="policyuser")
        self.policy_false = DummyPolicy.objects.create(
            result=False, wait_min=0, wait_max=1
        )
        self.policy_true = DummyPolicy.objects.create(
            result=True, wait_min=0, wait_max=1
        )
        self.policy_wrong_type = Policy.objects.create(name="wrong_type")
        self.policy_raises = ExpressionPolicy.objects.create(
            name="raises", expression="{{ 0/0 }}"
        )

    def test_engine_empty(self):
        """Ensure empty policy list passes"""
        pbm = PolicyBindingModel.objects.create()
        engine = PolicyEngine(pbm, self.user)
        result = engine.build().result
        self.assertEqual(result.passing, True)
        self.assertEqual(result.messages, ())

    def test_engine(self):
        """Ensure all policies passes (Mix of false and true -> false)"""
        pbm = PolicyBindingModel.objects.create()
        PolicyBinding.objects.create(target=pbm, policy=self.policy_false, order=0)
        PolicyBinding.objects.create(target=pbm, policy=self.policy_true, order=1)
        engine = PolicyEngine(pbm, self.user)
        result = engine.build().result
        self.assertEqual(result.passing, False)
        self.assertEqual(result.messages, ("dummy",))

    def test_engine_negate(self):
        """Test negate flag"""
        pbm = PolicyBindingModel.objects.create()
        PolicyBinding.objects.create(
            target=pbm, policy=self.policy_true, negate=True, order=0
        )
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
        with self.assertRaises(TypeError):
            engine = PolicyEngine(pbm, self.user)
            engine.build()

    def test_engine_cache(self):
        """Ensure empty policy list passes"""
        pbm = PolicyBindingModel.objects.create()
        PolicyBinding.objects.create(target=pbm, policy=self.policy_false, order=0)
        engine = PolicyEngine(pbm, self.user)
        self.assertEqual(len(cache.keys("policy_*")), 0)
        self.assertEqual(engine.build().passing, False)
        self.assertEqual(len(cache.keys("policy_*")), 1)
        self.assertEqual(engine.build().passing, False)
        self.assertEqual(len(cache.keys("policy_*")), 1)
