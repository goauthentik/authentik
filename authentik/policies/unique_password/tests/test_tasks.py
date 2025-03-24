from datetime import datetime, timedelta

from django.test import TestCase

from authentik.core.models import User
from authentik.core.tests.utils import create_test_user
from authentik.policies.models import PolicyBinding, PolicyBindingModel
from authentik.policies.unique_password.models import UniquePasswordPolicy, UserPasswordHistory
from authentik.policies.unique_password.tasks import (
    purge_password_history_table,
    trim_user_password_history,
)


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


class TestPurgePasswordHistory(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.create(username="testuser")

    def test_purge_password_history_table(self):
        """Tests the task empties the UserPasswordHistory table"""
        UserPasswordHistory.objects.bulk_create(
            [
                UserPasswordHistory(user=self.user, old_password="hunter1"),  # nosec B106
                UserPasswordHistory(user=self.user, old_password="hunter2"),  # nosec B106
            ]
        )
        purge_password_history_table.delay().get()
        self.assertFalse(UserPasswordHistory.objects.all())


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
                    old_password="hunter1",  # nosec B106
                    created_at=_now - timedelta(days=3),
                ),
                UserPasswordHistory(
                    user=self.user,
                    old_password="hunter2",  # nosec B106
                    created_at=_now - timedelta(days=2),
                ),
                UserPasswordHistory(
                    user=self.user,
                    old_password="hunter3",  # nosec B106
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
        trim_user_password_history(self.user.pk)
        user_pwd_history_qs = UserPasswordHistory.objects.filter(user=self.user)
        self.assertEqual(len(user_pwd_history_qs), 1)

    def test_trim_password_history_policy_diabled_no_op(self):
        """Test no passwords removed if policy binding is disabled"""

        # Insert a record to ensure it's not deleted after executing task
        UserPasswordHistory.objects.create(user=self.user, old_password="hunter2")  # nosec B106

        policy = UniquePasswordPolicy.objects.create(num_historical_passwords=1)
        PolicyBinding.objects.create(
            target=self.pbm,
            policy=policy,
            enabled=False,
            order=0,
        )
        trim_user_password_history(self.user.pk)
        self.assertTrue(UserPasswordHistory.objects.filter(user=self.user))

    def test_trim_password_history_fewer_records_than_maximum_is_no_op(self):
        """Test no passwords deleted if fewer passwords exist than limit"""

        UserPasswordHistory.objects.create(user=self.user, old_password="hunter2")  # nosec B106

        policy = UniquePasswordPolicy.objects.create(num_historical_passwords=2)
        PolicyBinding.objects.create(
            target=self.pbm,
            policy=policy,
            enabled=True,
            order=0,
        )
        trim_user_password_history(self.user.pk)
        self.assertTrue(UserPasswordHistory.objects.filter(user=self.user).exists())
