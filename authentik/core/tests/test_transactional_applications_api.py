"""Test Transactional API"""
from json import loads

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import OAuth2Provider


class TestTransactionalApplicationsAPI(APITestCase):
    """Test Transactional API"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()

    def test_create_transactional(self):
        """Test transactional Application + provider creation"""
        self.client.force_login(self.user)
        uid = generate_id()
        authorization_flow = create_test_flow()
        response = self.client.put(
            reverse("authentik_api:core-transactional-application"),
            data={
                "app": {
                    "name": uid,
                    "slug": uid,
                },
                "provider_model": "authentik_providers_oauth2.oauth2provider",
                "provider": {
                    "name": uid,
                    "authorization_flow": str(authorization_flow.pk),
                },
            },
        )
        response_body = loads(response.content.decode())
        self.assertTrue(response_body["valid"])
        self.assertTrue(response_body["applied"])
        provider = OAuth2Provider.objects.filter(name=uid).first()
        self.assertIsNotNone(provider)
        app = Application.objects.filter(slug=uid).first()
        self.assertIsNotNone(app)
        self.assertEqual(app.provider.pk, provider.pk)
