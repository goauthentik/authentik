"""authentik core task tests"""
from django.test import TestCase
from django.utils.timezone import now
from guardian.shortcuts import get_anonymous_user

from authentik.core.models import Token
from authentik.core.tasks import clean_expired_models


class TestTasks(TestCase):
    """Test Tasks"""

    def test_token_cleanup(self):
        """Test Token cleanup task"""
        Token.objects.create(expires=now(), user=get_anonymous_user())
        self.assertEqual(Token.objects.all().count(), 1)
        clean_expired_models.delay().get()
        self.assertEqual(Token.objects.all().count(), 0)
