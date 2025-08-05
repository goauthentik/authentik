from datetime import datetime, timedelta

from django.test import TestCase

from authentik.core.tests.utils import create_test_user
from authentik.enterprise.policies.unique_password.models import (
    UniquePasswordPolicy,
    UserPasswordHistory,
)
from authentik.enterprise.policies.unique_password.tasks import (
    check_and_purge_password_history,
    trim_password_histories,
)
from authentik.policies.models import PolicyBinding, PolicyBindingModel


class TestUniquePasswordPolicyModel(TestCase):
    """Test the UniquePasswordPolicy model methods"""

    def test_is_in_use_with_binding(self):
        """Test is_in_use returns True when a policy binding exists"""
        # Create a UniquePasswordPolicy and a PolicyBinding for it
        policy = UniquePasswordPolicy.objects.create(num_historical_passwords=5)
        pbm = PolicyBindingModel.objects.create()
        PolicyBinding.objects.create(target=pbm, policy=policy, order=0, enabled=True)

        # Verify is_in_use returns True
        self.assertTrue(UniquePasswordPolicy.is_in_use())

    def test_is_in_use_with_promptstage(self):
        """Test is_in_use returns True when attached to a PromptStage"""
        from authentik.stages.prompt.models import PromptStage

        # Create a UniquePasswordPolicy and attach it to a PromptStage
        policy = UniquePasswordPolicy.objects.create(num_historical_passwords=5)
        prompt_stage = PromptStage.objects.create(
            name="Test Prompt Stage",
        )
        # Use the set() method for many-to-many relationships
        prompt_stage.validation_policies.set([policy])

        # Verify is_in_use returns True
        self.assertTrue(UniquePasswordPolicy.is_in_use())


class TestTrimAllPasswordHistories(TestCase):
    """Test the task that trims password history for all users"""

    def setUp(self):
        self.user1 = create_test_user("test-user1")
        self.user2 = create_test_user("test-user2")
        self.pbm = PolicyBindingModel.objects.create()
        # Create a policy with a limit of 1 password
        self.policy = UniquePasswordPolicy.objects.create(num_historical_passwords=1)
        PolicyBinding.objects.create(
            target=self.pbm,
            policy=self.policy,
            enabled=True,
            order=0,
        )


class TestCheckAndPurgePasswordHistory(TestCase):
    """Test the scheduled task that checks if any policy is in use and purges if not"""

    def setUp(self):
        self.user = create_test_user("test-user")
        self.pbm = PolicyBindingModel.objects.create()

    def test_purge_when_no_policy_in_use(self):
        """Test that the task purges the table when no policy is in use"""
        # Create some password history entries
        UserPasswordHistory.create_for_user(self.user, "hunter2")

        # Verify we have entries
        self.assertTrue(UserPasswordHistory.objects.exists())

        # Run the task - should purge since no policy is in use
        check_and_purge_password_history.send()

        # Verify the table is empty
        self.assertFalse(UserPasswordHistory.objects.exists())

    def test_no_purge_when_policy_in_use(self):
        """Test that the task doesn't purge when a policy is in use"""
        # Create a policy and binding
        policy = UniquePasswordPolicy.objects.create(num_historical_passwords=5)
        PolicyBinding.objects.create(
            target=self.pbm,
            policy=policy,
            enabled=True,
            order=0,
        )

        # Create some password history entries
        UserPasswordHistory.create_for_user(self.user, "hunter2")

        # Verify we have entries
        self.assertTrue(UserPasswordHistory.objects.exists())

        # Run the task - should NOT purge since a policy is in use
        check_and_purge_password_history.send()

        # Verify the entries still exist
        self.assertTrue(UserPasswordHistory.objects.exists())


class TestTrimPasswordHistory(TestCase):
    """Test password history cleanup task"""

    def setUp(self):
        self.user = create_test_user("test-user")
        self.pbm = PolicyBindingModel.objects.create()

    def test_trim_password_history_ok(self):
        """Test passwords over the define limit are deleted"""
        _now = datetime.now()
        UserPasswordHistory.objects.bulk_create(
            [
                UserPasswordHistory(
                    user=self.user,
                    old_password="hunter1",  # nosec
                    created_at=_now - timedelta(days=3),
                ),
                UserPasswordHistory(
                    user=self.user,
                    old_password="hunter2",  # nosec
                    created_at=_now - timedelta(days=2),
                ),
                UserPasswordHistory(
                    user=self.user,
                    old_password="hunter3",  # nosec
                    created_at=_now,
                ),
            ]
        )

        policy = UniquePasswordPolicy.objects.create(num_historical_passwords=1)
        PolicyBinding.objects.create(
            target=self.pbm,
            policy=policy,
            enabled=True,
            order=0,
        )
        trim_password_histories.send()
        user_pwd_history_qs = UserPasswordHistory.objects.filter(user=self.user)
        self.assertEqual(len(user_pwd_history_qs), 1)

    def test_trim_password_history_policy_diabled_no_op(self):
        """Test no passwords removed if policy binding is disabled"""

        # Insert a record to ensure it's not deleted after executing task
        UserPasswordHistory.create_for_user(self.user, "hunter2")

        policy = UniquePasswordPolicy.objects.create(num_historical_passwords=1)
        PolicyBinding.objects.create(
            target=self.pbm,
            policy=policy,
            enabled=False,
            order=0,
        )
        trim_password_histories.send()
        self.assertTrue(UserPasswordHistory.objects.filter(user=self.user).exists())

    def test_trim_password_history_fewer_records_than_maximum_is_no_op(self):
        """Test no passwords deleted if fewer passwords exist than limit"""

        UserPasswordHistory.create_for_user(self.user, "hunter2")

        policy = UniquePasswordPolicy.objects.create(num_historical_passwords=2)
        PolicyBinding.objects.create(
            target=self.pbm,
            policy=policy,
            enabled=True,
            order=0,
        )
        trim_password_histories.send()
        self.assertTrue(UserPasswordHistory.objects.filter(user=self.user).exists())
