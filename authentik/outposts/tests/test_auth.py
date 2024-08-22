"""Test API Authentication"""

from django.conf import settings
from django.test import TestCase

from authentik.blueprints.tests import reconcile_app
from authentik.core.models import User, UserTypes
from authentik.outposts.apps import MANAGED_OUTPOST
from authentik.outposts.authentication import bearer_auth
from authentik.outposts.models import Outpost


class TestAPIAuth(TestCase):
    """Test API Authentication"""

    @reconcile_app("authentik_outposts")
    def test_managed_outpost_fail(self):
        """Test managed outpost"""
        outpost = Outpost.objects.filter(managed=MANAGED_OUTPOST).first()
        outpost.user.delete()
        outpost.delete()
        self.assertIsNone(bearer_auth(f"Bearer {settings.SECRET_KEY}".encode()))

    @reconcile_app("authentik_outposts")
    def test_managed_outpost_success(self):
        """Test managed outpost"""
        user: User = bearer_auth(f"Bearer {settings.SECRET_KEY}".encode())
        self.assertEqual(user.type, UserTypes.INTERNAL_SERVICE_ACCOUNT)
