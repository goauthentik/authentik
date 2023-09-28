"""proxy provider tests"""
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import ClientTypes
from authentik.providers.proxy.models import ProxyMode, ProxyProvider


class ProxyProviderTests(APITestCase):
    """proxy provider tests"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_basic_auth(self):
        """Test basic_auth_enabled"""
        response = self.client.post(
            reverse("authentik_api:proxyprovider-list"),
            {
                "name": generate_id(),
                "mode": ProxyMode.PROXY,
                "authorization_flow": create_test_flow().pk.hex,
                "external_host": "http://localhost",
                "internal_host": "http://localhost",
                "basic_auth_enabled": True,
                "basic_auth_user_attribute": generate_id(),
                "basic_auth_password_attribute": generate_id(),
            },
        )
        self.assertEqual(response.status_code, 201)

    def test_basic_auth_invalid(self):
        """Test basic_auth_enabled"""
        response = self.client.post(
            reverse("authentik_api:proxyprovider-list"),
            {
                "name": generate_id(),
                "mode": ProxyMode.PROXY,
                "authorization_flow": create_test_flow().pk.hex,
                "external_host": "http://localhost",
                "internal_host": "http://localhost",
                "basic_auth_enabled": True,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "basic_auth_enabled": [
                    "User and password attributes must be set when basic auth is enabled."
                ]
            },
        )

    def test_validate(self):
        """Test validate"""
        response = self.client.post(
            reverse("authentik_api:proxyprovider-list"),
            {
                "name": generate_id(),
                "mode": ProxyMode.PROXY,
                "authorization_flow": create_test_flow().pk.hex,
                "external_host": "http://localhost",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content.decode(),
            {"internal_host": ["Internal host cannot be empty when forward auth is disabled."]},
        )

    def test_create_defaults(self):
        """Test create"""
        name = generate_id()
        response = self.client.post(
            reverse("authentik_api:proxyprovider-list"),
            {
                "name": name,
                "mode": ProxyMode.PROXY,
                "authorization_flow": create_test_flow().pk.hex,
                "external_host": "http://localhost",
                "internal_host": "http://localhost",
            },
        )
        self.assertEqual(response.status_code, 201)
        provider: ProxyProvider = ProxyProvider.objects.get(name=name)
        self.assertEqual(provider.client_type, ClientTypes.CONFIDENTIAL)

    def test_update_defaults(self):
        """Test create"""
        name = generate_id()
        response = self.client.post(
            reverse("authentik_api:proxyprovider-list"),
            {
                "name": name,
                "mode": ProxyMode.PROXY,
                "authorization_flow": create_test_flow().pk.hex,
                "external_host": "http://localhost",
                "internal_host": "http://localhost",
            },
        )
        self.assertEqual(response.status_code, 201)
        provider: ProxyProvider = ProxyProvider.objects.get(name=name)
        self.assertEqual(provider.client_type, ClientTypes.CONFIDENTIAL)
        provider.client_type = ClientTypes.PUBLIC
        provider.save()
        response = self.client.put(
            reverse("authentik_api:proxyprovider-detail", kwargs={"pk": provider.pk}),
            {
                "name": name,
                "mode": ProxyMode.PROXY,
                "authorization_flow": create_test_flow().pk.hex,
                "external_host": "http://localhost",
                "internal_host": "http://localhost",
            },
        )
        self.assertEqual(response.status_code, 200)
        provider: ProxyProvider = ProxyProvider.objects.get(name=name)
        self.assertEqual(provider.client_type, ClientTypes.CONFIDENTIAL)
