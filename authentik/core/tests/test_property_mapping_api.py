"""Test property mappings API"""
from json import dumps

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import PropertyMapping, User


class TestPropertyMappingAPI(APITestCase):
    """Test property mappings API"""

    def setUp(self) -> None:
        super().setUp()
        self.mapping = PropertyMapping.objects.create(
            name="dummy", expression="""return {'foo': 'bar'}"""
        )
        self.user = User.objects.get(username="akadmin")
        self.client.force_login(self.user)

    def test_test_call(self):
        """Test Policy's test endpoint"""
        response = self.client.post(
            reverse(
                "authentik_api:propertymapping-test", kwargs={"pk": self.mapping.pk}
            ),
            data={
                "user": self.user.pk,
            },
        )
        self.assertJSONEqual(
            response.content.decode(),
            {"result": dumps({"foo": "bar"}), "successful": True},
        )
