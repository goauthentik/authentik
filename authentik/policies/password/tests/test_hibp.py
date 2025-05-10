"""Password Policy HIBP tests"""

from django.test import TestCase
from guardian.shortcuts import get_anonymous_user

from authentik.crypto.generators import generate_key
from authentik.policies.password.models import PasswordPolicy
from authentik.policies.types import PolicyRequest, PolicyResult
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT


class TestPasswordPolicyHIBP(TestCase):
    """Test Password Policy (haveibeenpwned)"""

    def test_invalid(self):
        """Test without password"""
        policy = PasswordPolicy.objects.create(
            check_have_i_been_pwned=True,
            check_static_rules=False,
            name="test_invalid",
        )
        request = PolicyRequest(get_anonymous_user())
        result: PolicyResult = policy.passes(request)
        self.assertFalse(result.passing)
        self.assertEqual(result.messages[0], "Password not set in context")

    def test_false(self):
        """Failing password case"""
        policy = PasswordPolicy.objects.create(
            check_have_i_been_pwned=True,
            check_static_rules=False,
            name="test_false",
        )
        request = PolicyRequest(get_anonymous_user())
        request.context[PLAN_CONTEXT_PROMPT] = {"password": "password"}  # nosec
        result: PolicyResult = policy.passes(request)
        self.assertFalse(result.passing)
        self.assertTrue(result.messages[0].startswith("Password exists on "))

    def test_true(self):
        """Positive password case"""
        policy = PasswordPolicy.objects.create(
            check_have_i_been_pwned=True,
            check_static_rules=False,
            name="test_true",
        )
        request = PolicyRequest(get_anonymous_user())
        request.context[PLAN_CONTEXT_PROMPT] = {"password": generate_key()}
        result: PolicyResult = policy.passes(request)
        self.assertTrue(result.passing)
        self.assertEqual(result.messages, tuple())
