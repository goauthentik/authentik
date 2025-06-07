"""Test property mappings API"""

from json import dumps

from django.urls import reverse
from rest_framework.serializers import ValidationError
from rest_framework.test import APITestCase

from authentik.core.api.property_mappings import PropertyMappingSerializer
from authentik.core.models import Group, PropertyMapping
from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id


class TestPropertyMappingAPI(APITestCase):
    """Test property mappings API"""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_test_call(self):
        """Test PropertyMappings's test endpoint"""
        mapping = PropertyMapping.objects.create(
            name="dummy", expression="""return {'foo': 'bar', 'baz': user.username}"""
        )
        response = self.client.post(
            reverse("authentik_api:propertymapping-test", kwargs={"pk": mapping.pk}),
            data={
                "user": self.user.pk,
            },
        )
        self.assertJSONEqual(
            response.content.decode(),
            {"result": dumps({"foo": "bar", "baz": self.user.username}), "successful": True},
        )

    def test_test_call_group(self):
        """Test PropertyMappings's test endpoint"""
        mapping = PropertyMapping.objects.create(
            name="dummy", expression="""return {'foo': 'bar', 'baz': group.name}"""
        )
        group = Group.objects.create(name=generate_id())
        response = self.client.post(
            reverse("authentik_api:propertymapping-test", kwargs={"pk": mapping.pk}),
            data={
                "group": group.pk,
            },
        )
        self.assertJSONEqual(
            response.content.decode(),
            {"result": dumps({"foo": "bar", "baz": group.name}), "successful": True},
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
