"""Test providers API"""

from json import loads

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import PropertyMapping
from authentik.core.tests.utils import create_test_admin_user


class TestProvidersAPI(APITestCase):
    """Test providers API"""

    def setUp(self) -> None:
        super().setUp()
        self.mapping = PropertyMapping.objects.create(
            name="dummy", expression="""return {'foo': 'bar'}"""
        )
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_types(self):
        """Test Providers's types endpoint"""
        response = self.client.get(
            reverse("authentik_api:provider-types"),
        )
        self.assertEqual(response.status_code, 200)

    def test_types_icon_themed_urls(self):
        """Test themed icon URLs of provider types"""
        response = self.client.get(reverse("authentik_api:provider-types"))

        types = {
            provider_type["model_name"]: provider_type for provider_type in loads(response.content)
        }
        self.assertEqual(
            types["proxyprovider"]["icon_themed_urls"],
            {
                "light": "/static/authentik/sources/proxy/light.svg",
                "dark": "/static/authentik/sources/proxy/dark.svg",
            },
        )
