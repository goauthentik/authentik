"""Test outpost service connection API"""
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import PropertyMapping, User


class TestOutpostServiceConnectionsAPI(APITestCase):
    """Test outpost service connection API"""

    def setUp(self) -> None:
        super().setUp()
        self.mapping = PropertyMapping.objects.create(
            name="dummy", expression="""return {'foo': 'bar'}"""
        )
        self.user = User.objects.get(username="akadmin")
        self.client.force_login(self.user)

    def test_types(self):
        """Test OutpostServiceConnections's types endpoint"""
        response = self.client.get(
            reverse("authentik_api:outpostserviceconnection-types"),
        )
        self.assertEqual(response.status_code, 200)
