"""Test tasks"""

from time import mktime

from django.utils.timezone import now
from guardian.shortcuts import get_anonymous_user
from rest_framework.test import APITestCase

from authentik.core.models import (
    USER_ATTRIBUTE_EXPIRES,
    USER_ATTRIBUTE_GENERATED,
    Token,
    TokenIntents,
    User,
)
from authentik.core.tasks import (
    clean_expired_models,
    clean_temporary_users,
)
from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id


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
        clean_expired_models.send()
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
        clean_temporary_users.send()
        self.assertFalse(User.objects.filter(username=username))
