"""Test API Utils"""

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    HyperlinkedModelSerializer,
)
from rest_framework.serializers import (
    ModelSerializer as BaseModelSerializer,
)
from rest_framework.test import APIRequestFactory, APITestCase

from authentik.core.api.utils import ModelSerializer as CustomModelSerializer
from authentik.core.api.utils import PrivilegedFieldsSerializerMixin, is_dict
from authentik.core.models import Group
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.lib.generators import generate_id
from authentik.lib.utils.reflection import all_subclasses
from authentik.rbac.models import Role


class TestAPIUtils(APITestCase):
    """Test API Utils"""

    def test_is_dict(self):
        """Test is_dict"""
        self.assertIsNone(is_dict({}))
        with self.assertRaises(ValidationError):
            is_dict("foo")

    def test_all_serializers_descend_from_custom(self):
        """Test that every serializer we define descends from our own ModelSerializer"""
        # Weirdly, there's only one serializer in `rest_framework` which descends from
        # ModelSerializer: HyperlinkedModelSerializer
        expected = {CustomModelSerializer, HyperlinkedModelSerializer}
        actual = set(all_subclasses(BaseModelSerializer)) - set(
            all_subclasses(CustomModelSerializer)
        )

        self.assertEqual(expected, actual)


class GroupPrivilegedSerializer(PrivilegedFieldsSerializerMixin, CustomModelSerializer):
    """Serializer that treats `attributes` as privileged, for testing the mixin"""

    privileged_fields = ["attributes"]

    class Meta:
        model = Group
        fields = ["name", "attributes"]


class TestPrivilegedFieldsSerializerMixin(APITestCase):
    """Test PrivilegedFieldsSerializerMixin"""

    def setUp(self):
        self.group = Group.objects.create(name=generate_id(), attributes={"private": generate_id()})

    def test_hidden_without_permission(self):
        """A caller without the object's view permission gets the field emptied"""
        request = APIRequestFactory().get("/")
        request.user = create_test_user()
        data = GroupPrivilegedSerializer(self.group, context={"request": request}).data
        self.assertEqual(data["attributes"], {})

    def test_visible_with_permission(self):
        """A caller granted the model's view permission sees the stored value"""
        user = create_test_user()
        role = Role.objects.create(name=generate_id())
        role.assign_perms("authentik_core.view_group")
        access_group = Group.objects.create(name=generate_id())
        access_group.roles.add(role)
        access_group.users.add(user)
        request = APIRequestFactory().get("/")
        request.user = user
        data = GroupPrivilegedSerializer(self.group, context={"request": request}).data
        self.assertEqual(data["attributes"], self.group.attributes)

    def test_visible_for_superuser(self):
        """A superuser sees the stored value"""
        request = APIRequestFactory().get("/")
        request.user = create_test_admin_user()
        data = GroupPrivilegedSerializer(self.group, context={"request": request}).data
        self.assertEqual(data["attributes"], self.group.attributes)

    def test_no_request_returns_field(self):
        """Without a request in context the mixin leaves the field untouched"""
        data = GroupPrivilegedSerializer(self.group).data
        self.assertEqual(data["attributes"], self.group.attributes)
