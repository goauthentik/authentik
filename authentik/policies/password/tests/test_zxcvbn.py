"""Password Policy zxcvbn tests"""

from django.test import TestCase
from guardian.shortcuts import get_anonymous_user

from authentik.crypto.generators import generate_key
from authentik.policies.password.models import PasswordPolicy
from authentik.policies.types import PolicyRequest, PolicyResult
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT


class TestPasswordPolicyZxcvbn(TestCase):
    """Test Password Policy (zxcvbn)"""

    def test_invalid(self):
        """Test without password"""
        policy = PasswordPolicy.objects.create(
            check_zxcvbn=True,
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
            check_zxcvbn=True,
            check_static_rules=False,
            zxcvbn_score_threshold=3,
            name="test_false",
        )
        request = PolicyRequest(get_anonymous_user())
        request.context[PLAN_CONTEXT_PROMPT] = {"password": "password"}  # nosec
        result: PolicyResult = policy.passes(request)
        self.assertFalse(result.passing, result.messages)
        self.assertEqual(result.messages[0], "Password is too weak.")
        self.assertEqual(result.messages[1], "Add another word or two. Uncommon words are better.")

        request.context[PLAN_CONTEXT_PROMPT] = {"password": "Awdccdw1234"}  # nosec
        result: PolicyResult = policy.passes(request)
        self.assertFalse(result.passing, result.messages)
        self.assertEqual(result.messages[0], "Password is too weak.")
        self.assertEqual(len(result.messages), 1)

    def test_true(self):
        """Positive password case"""
        policy = PasswordPolicy.objects.create(
            check_zxcvbn=True,
            check_static_rules=False,
            name="test_true",
        )
        request = PolicyRequest(get_anonymous_user())
        request.context[PLAN_CONTEXT_PROMPT] = {"password": generate_key()}
        result: PolicyResult = policy.passes(request)
        self.assertTrue(result.passing)
        self.assertEqual(result.messages, tuple())
