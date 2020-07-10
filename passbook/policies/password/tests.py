"""Password Policy tests"""
from django.test import TestCase
from guardian.shortcuts import get_anonymous_user

from passbook.policies.password.models import PasswordPolicy
from passbook.policies.types import PolicyRequest, PolicyResult


class TestPasswordPolicy(TestCase):
    """Test Password Policy"""

    def test_false(self):
        """Failing password case"""
        policy = PasswordPolicy.objects.create(
            name="test_false",
            amount_uppercase=1,
            amount_lowercase=2,
            amount_symbols=3,
            length_min=24,
            error_message="test message",
        )
        request = PolicyRequest(get_anonymous_user())
        request.context["password"] = "test"
        result: PolicyResult = policy.passes(request)
        self.assertFalse(result.passing)
        self.assertEqual(result.messages, ("test message",))

    def test_true(self):
        """Positive password case"""
        policy = PasswordPolicy.objects.create(
            name="test_true",
            amount_uppercase=1,
            amount_lowercase=2,
            amount_symbols=3,
            length_min=3,
            error_message="test message",
        )
        request = PolicyRequest(get_anonymous_user())
        request.context["password"] = "Test()!"
        result: PolicyResult = policy.passes(request)
        self.assertTrue(result.passing)
        self.assertEqual(result.messages, tuple())
