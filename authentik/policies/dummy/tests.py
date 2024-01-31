"""dummy policy tests"""

from django.test import TestCase
from guardian.shortcuts import get_anonymous_user

from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.engine import PolicyRequest


class TestDummyPolicy(TestCase):
    """Test dummy policy"""

    def setUp(self):
        super().setUp()
        self.request = PolicyRequest(user=get_anonymous_user())

    def test_policy(self):
        """test policy .passes"""
        policy: DummyPolicy = DummyPolicy.objects.create(name="dummy", wait_min=1, wait_max=2)
        result = policy.passes(self.request)
        self.assertFalse(result.passing)
        self.assertEqual(result.messages, ("dummy",))
