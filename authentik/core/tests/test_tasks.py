"""Test tasks"""

from datetime import timedelta
from time import mktime

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils.timezone import now
from django_channels_postgres.models import GroupChannel, Message
from django_postgres_cache.models import CacheEntry
from guardian.shortcuts import get_anonymous_user
from rest_framework.test import APITestCase

from authentik.core.models import (
    USER_ATTRIBUTE_EXPIRES,
    USER_ATTRIBUTE_GENERATED,
    Actor,
    ActorPolicyInheritance,
    Token,
    TokenIntents,
    User,
)
from authentik.core.tasks import (
    clean_expired_models,
    clean_temporary_users,
)
from authentik.core.tests.utils import create_test_admin_user
from authentik.events.models import Event, EventAction
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

    def test_token_expire_actor(self):
        """Test Token expire task deletes (rather than rotates) an actor's token"""
        actor = Actor.for_user(None, ActorPolicyInheritance.NONE)
        token: Token = Token.objects.create(
            expires=now(), user=actor, intent=TokenIntents.INTENT_API
        )
        clean_expired_models.send()
        self.assertFalse(Token.objects.filter(pk=token.pk).exists())

    def test_clean_expired_storage(self):
        """The task deletes expired storage records while retaining live records."""
        for model, fields in (
            (CacheEntry, {"cache_key": "cleanup-test", "value": "value"}),
            (Message, {"channel": "cleanup-test", "message": b"message"}),
            (GroupChannel, {"channel": "cleanup-test", "group_key": "cleanup-test"}),
        ):
            with self.subTest(model=model):
                expired = model.objects.create(expires=now() - timedelta(hours=1), **fields)
                live_fields = {**fields}
                if model is CacheEntry:
                    live_fields["cache_key"] = "cleanup-test-live"
                live = model.objects.create(expires=now() + timedelta(hours=1), **live_fields)
                clean_expired_models.send()
                self.assertFalse(model.objects.filter(pk=expired.pk).exists())
                self.assertTrue(model.objects.filter(pk=live.pk).exists())

    def test_expire_bulk(self):
        """Test that many expired objects are deleted in batches, not one query per object"""
        Event.objects.all().delete()
        Event.objects.bulk_create(
            Event(action=EventAction.CUSTOM_PREFIX, app="test", expires=now()) for _ in range(2_500)
        )
        with CaptureQueriesContext(connection) as ctx:
            clean_expired_models.send()
        self.assertFalse(Event.objects.including_expired().exists())
        self.assertLessEqual(len(ctx.captured_queries), 500)

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
