"""Test property mappings API"""

from json import dumps

from django.urls import reverse
from rest_framework.serializers import ValidationError
from rest_framework.test import APITestCase

from authentik.core.api.property_mappings import PropertyMappingSerializer
from authentik.core.models import Group, PropertyMapping
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import ScopeMapping


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
        """Test PropertyMapping's types endpoint"""
        response = self.client.get(
            reverse("authentik_api:propertymapping-types"),
        )
        self.assertEqual(response.status_code, 200)


class TestPropertyMappingAPIPermissions(APITestCase):
    """Object permissions on `propertymappings/all/` for a mapping of another app"""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_user()
        self.other_user = create_test_user()
        self.mapping = ScopeMapping.objects.create(
            name=generate_id(), scope_name=generate_id(), expression="return {'foo': 'bar'}"
        )
        self.client.force_login(self.user)

    def post_test(self):
        return self.client.post(
            reverse("authentik_api:propertymapping-test", kwargs={"pk": self.mapping.pk}),
            data={"user": self.other_user.pk},
        )

    def test_test_call_global(self):
        """Test a subclass' mapping with the base model's global permissions"""
        self.user.assign_perms_to_managed_role("authentik_core.view_propertymapping")
        self.user.assign_perms_to_managed_role("authentik_core.add_propertymapping")
        self.user.assign_perms_to_managed_role("authentik_core.view_user")
        response = self.post_test()
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode(), {"result": dumps({"foo": "bar"}), "successful": True}
        )

    def test_test_call_denied(self):
        """Testing a subclass' mapping without the permissions is refused (not a server error)"""
        self.assertEqual(self.post_test().status_code, 403)
        self.user.assign_perms_to_managed_role("authentik_core.view_propertymapping")
        self.user.assign_perms_to_managed_role("authentik_core.view_user")
        self.assertEqual(self.post_test().status_code, 403)

    def test_destroy_denied(self):
        """Deleting a subclass' mapping without the permission is refused (not a server error)"""
        self.user.assign_perms_to_managed_role("authentik_core.view_propertymapping")
        response = self.client.delete(
            reverse("authentik_api:propertymapping-detail", kwargs={"pk": self.mapping.pk})
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(ScopeMapping.objects.filter(pk=self.mapping.pk).exists())
