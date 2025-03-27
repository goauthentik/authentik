"""Test providers API"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.api.providers import ProviderSerializer
from authentik.core.models import Application, PropertyMapping, Provider
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

    def test_provider_serializer_without_application(self):
        """Test that Provider serializer handles missing application gracefully"""
        # Create a provider without an application
        provider = Provider.objects.create(name="test-provider")

        serializer = ProviderSerializer(instance=provider)
        serialized_data = serializer.data

        # Check that fields return empty strings when no application exists
        self.assertEqual(serialized_data["assigned_application_slug"], "")
        self.assertEqual(serialized_data["assigned_application_name"], "")
        self.assertEqual(serialized_data["assigned_backchannel_application_slug"], "")
        self.assertEqual(serialized_data["assigned_backchannel_application_name"], "")

    def test_provider_serializer_with_application(self):
        """Test that Provider serializer correctly includes application data"""
        # Create an application
        app = Application.objects.create(name="Test App", slug="test-app")

        # Create a provider with an application
        provider = Provider.objects.create(name="test-provider-with-app")
        app.provider = provider
        app.save()

        serializer = ProviderSerializer(instance=provider)
        serialized_data = serializer.data

        # Check that fields return correct values when application exists
        self.assertEqual(serialized_data["assigned_application_slug"], "test-app")
        self.assertEqual(serialized_data["assigned_application_name"], "Test App")
        self.assertEqual(serialized_data["assigned_backchannel_application_slug"], "")
        self.assertEqual(serialized_data["assigned_backchannel_application_name"], "")

    def test_provider_api_response(self):
        """Test that the API response includes empty strings for missing applications"""
        # Create a provider without an application
        provider = Provider.objects.create(name="test-provider-api")

        response = self.client.get(
            reverse("authentik_api:provider-detail", kwargs={"pk": provider.pk}),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["assigned_application_slug"], "")
        self.assertEqual(response.data["assigned_application_name"], "")
        self.assertEqual(response.data["assigned_backchannel_application_slug"], "")
        self.assertEqual(response.data["assigned_backchannel_application_name"], "")
