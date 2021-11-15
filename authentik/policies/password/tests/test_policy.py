"""Password Policy tests"""
from django.test import TestCase
from guardian.shortcuts import get_anonymous_user

from authentik.lib.generators import generate_key
from authentik.policies.password.models import PasswordPolicy
from authentik.policies.types import PolicyRequest, PolicyResult


class TestPasswordPolicy(TestCase):
    """Test Password Policy"""

    def setUp(self) -> None:
        self.policy = PasswordPolicy.objects.create(
            name="test_false",
            amount_uppercase=1,
            amount_lowercase=2,
            amount_symbols=3,
            length_min=24,
            error_message="test message",
        )

    def test_invalid(self):
        """Test without password"""
        request = PolicyRequest(get_anonymous_user())
        result: PolicyResult = self.policy.passes(request)
        self.assertFalse(result.passing)
        self.assertEqual(result.messages[0], "Password not set in context")

    def test_failed_length(self):
        """Password too short"""
        request = PolicyRequest(get_anonymous_user())
        request.context["password"] = "test"  # nosec
        result: PolicyResult = self.policy.passes(request)
        self.assertFalse(result.passing)
        self.assertEqual(result.messages, ("test message",))

    def test_failed_lowercase(self):
        """not enough lowercase"""
        request = PolicyRequest(get_anonymous_user())
        request.context["password"] = "TTTTTTTTTTTTTTTTTTTTTTTe"  # nosec
        result: PolicyResult = self.policy.passes(request)
        self.assertFalse(result.passing)
        self.assertEqual(result.messages, ("test message",))

    def test_failed_uppercase(self):
        """not enough uppercase"""
        request = PolicyRequest(get_anonymous_user())
        request.context["password"] = "tttttttttttttttttttttttE"  # nosec
        result: PolicyResult = self.policy.passes(request)
        self.assertFalse(result.passing)
        self.assertEqual(result.messages, ("test message",))

    def test_failed_symbols(self):
        """not enough uppercase"""
        request = PolicyRequest(get_anonymous_user())
        request.context["password"] = "TETETETETETETETETETETETETe!!!"  # nosec
        result: PolicyResult = self.policy.passes(request)
        self.assertFalse(result.passing)
        self.assertEqual(result.messages, ("test message",))

    def test_true(self):
        """Positive password case"""
        request = PolicyRequest(get_anonymous_user())
        request.context["password"] = generate_key() + "ee!!!"  # nosec
        result: PolicyResult = self.policy.passes(request)
        self.assertTrue(result.passing)
        self.assertEqual(result.messages, tuple())
