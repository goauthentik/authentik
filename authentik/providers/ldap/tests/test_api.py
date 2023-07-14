"""LDAP Provider API tests"""
from json import loads

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.ldap.models import LDAPProvider


class TestLDAPProviderAPI(APITestCase):
    """LDAP Provider API tests"""

    def test_outpost_application(self):
        """Test outpost-like provider retrieval (direct connection)"""
        provider = LDAPProvider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
        )
        Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider=provider,
        )
        user = create_test_admin_user()
        self.client.force_login(user)
        res = self.client.get(reverse("authentik_api:ldapprovideroutpost-list"))
        self.assertEqual(res.status_code, 200)
        data = loads(res.content.decode())
        self.assertEqual(data["pagination"]["count"], 1)
        self.assertEqual(len(data["results"]), 1)

    def test_outpost_application_backchannel(self):
        """Test outpost-like provider retrieval (backchannel connection)"""
        provider = LDAPProvider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
        )
        app: Application = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        app.backchannel_providers.add(provider)
        user = create_test_admin_user()
        self.client.force_login(user)
        res = self.client.get(reverse("authentik_api:ldapprovideroutpost-list"))
        self.assertEqual(res.status_code, 200)
        data = loads(res.content.decode())
        self.assertEqual(data["pagination"]["count"], 1)
        self.assertEqual(len(data["results"]), 1)
