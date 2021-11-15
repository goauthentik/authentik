"""HIBP Policy tests"""
from django.test import TestCase
from guardian.shortcuts import get_anonymous_user

from authentik.lib.generators import generate_key
from authentik.policies.hibp.models import HaveIBeenPwendPolicy
from authentik.policies.types import PolicyRequest, PolicyResult


class TestHIBPPolicy(TestCase):
    """Test HIBP Policy"""

    def test_invalid(self):
        """Test without password"""
        policy = HaveIBeenPwendPolicy.objects.create(
            name="test_invalid",
        )
        request = PolicyRequest(get_anonymous_user())
        result: PolicyResult = policy.passes(request)
        self.assertFalse(result.passing)
        self.assertEqual(result.messages[0], "Password not set in context")

    def test_false(self):
        """Failing password case"""
        policy = HaveIBeenPwendPolicy.objects.create(
            name="test_false",
        )
        request = PolicyRequest(get_anonymous_user())
        request.context["password"] = "password"  # nosec
        result: PolicyResult = policy.passes(request)
        self.assertFalse(result.passing)
        self.assertTrue(result.messages[0].startswith("Password exists on "))

    def test_true(self):
        """Positive password case"""
        policy = HaveIBeenPwendPolicy.objects.create(
            name="test_true",
        )
        request = PolicyRequest(get_anonymous_user())
        request.context["password"] = generate_key()
        result: PolicyResult = policy.passes(request)
        self.assertTrue(result.passing)
        self.assertEqual(result.messages, tuple())
