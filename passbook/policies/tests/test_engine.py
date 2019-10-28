"""policy engine tests"""
from django.core.cache import cache
from django.test import TestCase

from passbook.core.models import DebugPolicy, Policy, User
from passbook.policies.engine import PolicyEngine


class PolicyTestEngine(TestCase):
    """PolicyEngine tests"""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="policyuser")
        self.policy_false = DebugPolicy.objects.create(
            result=False,
            wait_min=0,
            wait_max=1)
        self.policy_true = DebugPolicy.objects.create(
            result=True,
            wait_min=0,
            wait_max=1)
        self.policy_negate = DebugPolicy.objects.create(
            negate=True,
            result=True,
            wait_min=0,
            wait_max=1)
        self.policy_raises = Policy.objects.create(
            name='raises')

    def test_engine_empty(self):
        """Ensure empty policy list passes"""
        engine = PolicyEngine([], self.user)
        self.assertEqual(engine.build().passing, True)

    def test_engine(self):
        """Ensure all policies passes (Mix of false and true -> false)"""
        engine = PolicyEngine(DebugPolicy.objects.filter(negate__exact=False), self.user)
        self.assertEqual(engine.build().passing, False)

    def test_engine_negate(self):
        """Test negate flag"""
        engine = PolicyEngine(DebugPolicy.objects.filter(negate__exact=True), self.user)
        self.assertEqual(engine.build().passing, False)

    def test_engine_policy_error(self):
        """Test negate flag"""
        engine = PolicyEngine(Policy.objects.filter(name='raises'), self.user)
        self.assertEqual(engine.build().passing, False)

    def test_engine_cache(self):
        """Ensure empty policy list passes"""
        engine = PolicyEngine(DebugPolicy.objects.filter(negate__exact=False), self.user)
        self.assertEqual(len(cache.keys('policy_*')), 0)
        self.assertEqual(engine.build().passing, False)
        self.assertEqual(len(cache.keys('policy_*')), 2)
        self.assertEqual(engine.build().passing, False)
        self.assertEqual(len(cache.keys('policy_*')), 2)
