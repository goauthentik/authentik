"""Test AuthenticatedSessions API"""

from json import loads

from django.urls.base import reverse
from rest_framework.test import APITestCase

from authentik.core.models import AuthenticatedSession, Session, User
from authentik.core.tests.utils import create_test_admin_user


class TestAuthenticatedSessionsAPI(APITestCase):
    """Test AuthenticatedSessions API"""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.other_user = User.objects.create(username="normal-user")

    def test_list(self):
        """Test session list endpoint"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("authentik_api:authenticatedsession-list"))
        self.assertEqual(response.status_code, 200)

    def test_non_admin_list(self):
        """Test non-admin list"""
        self.client.force_login(self.other_user)
        response = self.client.get(reverse("authentik_api:authenticatedsession-list"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertEqual(body["pagination"]["count"], 1)

    def test_delete(self):
        """Test deletion"""
        self.client.force_login(self.user)
        self.assertEqual(AuthenticatedSession.objects.all().count(), 1)
        self.assertEqual(Session.objects.all().count(), 1)
        response = self.client.delete(
            reverse(
                "authentik_api:authenticatedsession-detail",
                kwargs={"uuid": AuthenticatedSession.objects.first().uuid},
            )
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(AuthenticatedSession.objects.all().count(), 0)
        self.assertEqual(Session.objects.all().count(), 0)
