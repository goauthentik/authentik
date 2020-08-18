"""HIBP Policy tests"""
from django.test import TestCase
from guardian.shortcuts import get_anonymous_user

from passbook.policies.hibp.models import HaveIBeenPwendPolicy
from passbook.policies.types import PolicyRequest, PolicyResult
from passbook.providers.oauth2.generators import generate_client_secret


class TestHIBPPolicy(TestCase):
    """Test HIBP Policy"""

    def test_false(self):
        """Failing password case"""
        policy = HaveIBeenPwendPolicy.objects.create(name="test_false",)
        request = PolicyRequest(get_anonymous_user())
        request.context["password"] = "password"
        result: PolicyResult = policy.passes(request)
        self.assertFalse(result.passing)
        self.assertTrue(result.messages[0].startswith("Password exists on "))

    def test_true(self):
        """Positive password case"""
        policy = HaveIBeenPwendPolicy.objects.create(name="test_true",)
        request = PolicyRequest(get_anonymous_user())
        request.context["password"] = generate_client_secret()
        result: PolicyResult = policy.passes(request)
        self.assertTrue(result.passing)
        self.assertEqual(result.messages, tuple())
