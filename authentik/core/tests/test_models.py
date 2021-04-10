"""authentik core models tests"""
from time import sleep

from django.test import TestCase
from django.utils.timezone import now
from guardian.shortcuts import get_anonymous_user

from authentik.core.models import Token


class TestModels(TestCase):
    """Test Models"""

    def test_token_expire(self):
        """Test token expiring"""
        token = Token.objects.create(expires=now(), user=get_anonymous_user())
        sleep(0.5)
        self.assertTrue(token.is_expired)

    def test_token_expire_no_expire(self):
        """Test token expiring with "expiring" set """
        token = Token.objects.create(
            expires=now(), user=get_anonymous_user(), expiring=False
        )
        sleep(0.5)
        self.assertFalse(token.is_expired)
