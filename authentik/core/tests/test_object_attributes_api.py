"""Test object attributes API"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.api.object_attributes import ContentType
from authentik.core.models import ObjectAttribute, User
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.lib.generators import generate_id


class TestObjectAttributesAPI(APITestCase):
    """Test object attributes API"""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_create(self):
        res = self.client.post(
            reverse("authentik_api:objectattribute-list"),
            data={
                "object_type": "authentik_core.user",
                "enabled": False,
                "key": "employeeNumber",
                "label": "Employee Number",
                "type": "text",
                "group": "Employee",
                "is_unique": False,
                "is_required": False,
            },
        )
        self.assertEqual(res.status_code, 201)
        attr = ObjectAttribute.objects.filter(key="employeeNumber").first()
        self.assertIsNotNone(attr)

    def test_create_invalid(self):
        res = self.client.post(
            reverse("authentik_api:objectattribute-list"),
            data={
                "object_type": "authentik_core.objectattribute",
                "enabled": False,
                "key": "employeeNumber",
                "label": "Employee Number",
                "type": "text",
                "group": "Employee",
                "is_unique": False,
                "is_required": False,
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(res.content, {"object_type": ["Invalid object type"]})

    def test_create_invalid_array_unique(self):
        res = self.client.post(
            reverse("authentik_api:objectattribute-list"),
            data={
                "object_type": "authentik_core.user",
                "enabled": False,
                "key": "employeeNumber",
                "label": "Employee Number",
                "type": "text",
                "group": "Employee",
                "is_unique": True,
                "is_required": False,
                "is_array": True,
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(
            res.content, {"non_field_errors": ["Unique cannot be enabled for arrays."]}
        )

    def test_update(self):
        attr = ObjectAttribute.objects.create(
            object_type=ContentType.objects.get_for_model(User),
            label="foo",
            key=generate_id(),
            type=ObjectAttribute.AttributeType.TEXT,
        )
        res = self.client.put(
            reverse("authentik_api:objectattribute-detail", kwargs={"pk": attr.pk}),
            data={
                "object_type": "authentik_core.user",
                "enabled": False,
                "key": attr.key,
                "label": "Employee Number",
                "type": "text",
                "group": "Employee",
                "is_unique": False,
                "is_required": False,
            },
        )
        self.assertEqual(res.status_code, 200)
        attr.refresh_from_db()
        self.assertEqual(attr.label, "Employee Number")

    def test_user_attrib_validation_required(self):
        attr = ObjectAttribute.objects.create(
            object_type=ContentType.objects.get_for_model(User),
            label="foo",
            key=generate_id(),
            type=ObjectAttribute.AttributeType.TEXT,
            is_required=True,
        )
        res = self.client.patch(
            reverse("authentik_api:user-detail", kwargs={"pk": self.user.pk}),
            data={
                "attributes": {},
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(res.content, {f"attributes_{attr.key}": ["This field is required"]})

    def test_user_attrib_validation_unique(self):
        attr = ObjectAttribute.objects.create(
            object_type=ContentType.objects.get_for_model(User),
            label="foo",
            key=generate_id(),
            type=ObjectAttribute.AttributeType.TEXT,
            is_unique=True,
        )
        other_user = create_test_user()
        other_user.attributes[attr.key] = "foo"
        other_user.save()
        res = self.client.patch(
            reverse("authentik_api:user-detail", kwargs={"pk": self.user.pk}),
            data={
                "attributes": {attr.key: "foo"},
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(res.content, {f"attributes_{attr.key}": ["Value is not unique."]})

    def test_user_attrib_validation_regex(self):
        attr = ObjectAttribute.objects.create(
            object_type=ContentType.objects.get_for_model(User),
            label="foo",
            key=generate_id(),
            type=ObjectAttribute.AttributeType.TEXT,
            regex="bar",
        )
        res = self.client.patch(
            reverse("authentik_api:user-detail", kwargs={"pk": self.user.pk}),
            data={
                "attributes": {attr.key: "foo"},
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(
            res.content, {f"attributes_{attr.key}": ["Value does not match configured pattern."]}
        )

    def test_user_attrib_validation_array(self):
        attr = ObjectAttribute.objects.create(
            object_type=ContentType.objects.get_for_model(User),
            label="foo",
            key=generate_id(),
            type=ObjectAttribute.AttributeType.TEXT,
            is_array=True,
        )
        res = self.client.patch(
            reverse("authentik_api:user-detail", kwargs={"pk": self.user.pk}),
            data={
                "attributes": {attr.key: "foo"},
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(res.content, {f"attributes_{attr.key}": ["Value must be an array."]})

        res = self.client.patch(
            reverse("authentik_api:user-detail", kwargs={"pk": self.user.pk}),
            data={
                "attributes": {attr.key: ["foo"]},
            },
        )
        self.assertEqual(res.status_code, 200)

    def test_user_attrib_validation_array_regex(self):
        attr = ObjectAttribute.objects.create(
            object_type=ContentType.objects.get_for_model(User),
            label="foo",
            key=generate_id(),
            type=ObjectAttribute.AttributeType.TEXT,
            is_array=True,
            regex="bar",
        )
        res = self.client.patch(
            reverse("authentik_api:user-detail", kwargs={"pk": self.user.pk}),
            data={
                "attributes": {attr.key: ["foo"]},
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(
            res.content, {f"attributes_{attr.key}": ["Value does not match configured pattern."]}
        )
