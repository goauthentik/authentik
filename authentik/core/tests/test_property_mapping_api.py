"""Test property mappings API"""

from json import dumps

from django.urls import reverse
from rest_framework.serializers import ValidationError
from rest_framework.test import APITestCase

from authentik.core.api.propertymappings import PropertyMappingSerializer
from authentik.core.models import PropertyMapping
from authentik.core.tests.utils import create_test_admin_user


class TestPropertyMappingAPI(APITestCase):
    """Test property mappings API"""

    def setUp(self) -> None:
        super().setUp()
        self.mapping = PropertyMapping.objects.create(
            name="dummy", expression="""return {'foo': 'bar'}"""
        )
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_test_call(self):
        """Test PropertMappings's test endpoint"""
        response = self.client.post(
            reverse("authentik_api:propertymapping-test", kwargs={"pk": self.mapping.pk}),
            data={
                "user": self.user.pk,
            },
        )
        self.assertJSONEqual(
            response.content.decode(),
            {"result": dumps({"foo": "bar"}), "successful": True},
        )

    def test_validate(self):
        """Test PropertyMappings's validation"""
        # Because the root property-mapping has no write operation, we just instantiate
        # a serializer and test inline
        expr = "return True"
        self.assertEqual(PropertyMappingSerializer().validate_expression(expr), expr)
        with self.assertRaises(ValidationError):
            PropertyMappingSerializer().validate_expression("/")

    def test_types(self):
        """Test PropertyMappigns's types endpoint"""
        response = self.client.get(
            reverse("authentik_api:propertymapping-types"),
        )
        self.assertEqual(response.status_code, 200)
