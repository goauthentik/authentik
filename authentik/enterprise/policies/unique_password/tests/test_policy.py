"""Unique Password Policy tests"""

from django.contrib.auth.hashers import make_password
from django.test import TestCase
from guardian.shortcuts import get_anonymous_user

from authentik.core.models import User
from authentik.enterprise.policies.unique_password.models import (
    UniquePasswordPolicy,
    UserPasswordHistory,
)
from authentik.policies.types import PolicyRequest, PolicyResult
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT


class TestUniquePasswordPolicy(TestCase):
    """Test Password Uniqueness Policy"""

    def setUp(self) -> None:
        self.policy = UniquePasswordPolicy.objects.create(
            name="test_unique_password", num_historical_passwords=1
        )
        self.user = User.objects.create(username="test-user")

    def test_invalid(self):
        """Test without password present in request"""
        request = PolicyRequest(get_anonymous_user())
        result: PolicyResult = self.policy.passes(request)
        self.assertFalse(result.passing)
        self.assertEqual(result.messages[0], "Password not set in context")

    def test_passes_no_previous_passwords(self):
        request = PolicyRequest(get_anonymous_user())
        request.context = {PLAN_CONTEXT_PROMPT: {"password": "hunter2"}}
        result: PolicyResult = self.policy.passes(request)
        self.assertTrue(result.passing)

    def test_passes_passwords_are_different(self):
        # Seed database with an old password
        UserPasswordHistory.objects.create(user=self.user, old_password=make_password("hunter1"))

        request = PolicyRequest(self.user)
        request.context = {PLAN_CONTEXT_PROMPT: {"password": "hunter2"}}
        result: PolicyResult = self.policy.passes(request)
        self.assertTrue(result.passing)

    def test_passes_multiple_old_passwords(self):
        # Seed with multiple old passwords
        UserPasswordHistory.objects.bulk_create(
            [
                UserPasswordHistory(user=self.user, old_password=make_password("hunter1")),
                UserPasswordHistory(user=self.user, old_password=make_password("hunter2")),
            ]
        )
        request = PolicyRequest(self.user)
        request.context = {PLAN_CONTEXT_PROMPT: {"password": "hunter3"}}
        result: PolicyResult = self.policy.passes(request)
        self.assertTrue(result.passing)

    def test_fails_password_matches_old_password(self):
        # Seed database with an old password

        UserPasswordHistory.objects.create(user=self.user, old_password=make_password("hunter1"))

        request = PolicyRequest(self.user)
        request.context = {PLAN_CONTEXT_PROMPT: {"password": "hunter1"}}
        result: PolicyResult = self.policy.passes(request)
        self.assertFalse(result.passing)

    def test_fails_if_identical_password_with_different_hash_algos(self):
        UserPasswordHistory.objects.create(
            user=self.user,
            old_password=make_password("hunter2", "somesalt", "scrypt"),
        )
        request = PolicyRequest(self.user)
        request.context = {PLAN_CONTEXT_PROMPT: {"password": "hunter2"}}
        result: PolicyResult = self.policy.passes(request)
        self.assertFalse(result.passing)
