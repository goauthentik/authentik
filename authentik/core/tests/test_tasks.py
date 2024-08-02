"""Test tasks"""

from datetime import datetime, timedelta
from time import mktime

from django.test import TestCase
from django.utils.timezone import now
from guardian.shortcuts import get_anonymous_user
from rest_framework.test import APITestCase

from authentik.core.models import (
    USER_ATTRIBUTE_EXPIRES,
    USER_ATTRIBUTE_GENERATED,
    Token,
    TokenIntents,
    User,
    UserPasswordHistory,
)
from authentik.core.tasks import (
    clean_expired_models,
    clean_temporary_users,
    purge_password_history_table,
    trim_user_password_history,
)
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.lib.generators import generate_id
from authentik.policies.models import PolicyBinding, PolicyBindingModel
from authentik.policies.unique_password.models import UniquePasswordPolicy


class TestTasks(APITestCase):
    """Test token API"""

    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.create(username="testuser")
        self.admin = create_test_admin_user()
        self.client.force_login(self.user)

    def test_token_expire(self):
        """Test Token expire task"""
        token: Token = Token.objects.create(
            expires=now(), user=get_anonymous_user(), intent=TokenIntents.INTENT_API
        )
        key = token.key
        clean_expired_models.delay().get()
        token.refresh_from_db()
        self.assertNotEqual(key, token.key)

    def test_clean_temporary_users(self):
        """Test clean_temporary_users task"""
        username = generate_id
        User.objects.create(
            username=username,
            attributes={
                USER_ATTRIBUTE_GENERATED: True,
                USER_ATTRIBUTE_EXPIRES: mktime(now().timetuple()),
            },
        )
        clean_temporary_users.delay().get()
        self.assertFalse(User.objects.filter(username=username))

    def test_purge_password_history_table(self):
        """Tests the task empties the core.models.UserPasswordHistory table"""
        UserPasswordHistory.objects.bulk_create(
            [
                UserPasswordHistory(user=self.user, change={"old_password": "hunter1"}),
                UserPasswordHistory(user=self.user, change={"old_password": "hunter2"}),
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
        """Test passwors over the define limit are deleted"""
        _now = datetime.now()
        UserPasswordHistory.objects.bulk_create(
            [
                UserPasswordHistory(
                    user=self.user,
                    change={"old_password": "hunter1"},
                    created_at=_now - timedelta(days=3),
                ),
                UserPasswordHistory(
                    user=self.user,
                    change={"old_password": "hunter2"},
                    created_at=_now - timedelta(days=2),
                ),
                UserPasswordHistory(
                    user=self.user, change={"old_password": "hunter3"}, created_at=_now
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
        UserPasswordHistory.objects.create(user=self.user, change={"old_password": "hunter2"})

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

        UserPasswordHistory.objects.create(user=self.user, change={"old_password": "hunter2"})

        policy = UniquePasswordPolicy.objects.create(num_historical_passwords=2)
        PolicyBinding.objects.create(
            target=self.pbm,
            policy=policy,
            enabled=True,
            order=0,
        )
        trim_user_password_history(self.user.pk)
        self.assertTrue(UserPasswordHistory.objects.filter(user=self.user).exists())
