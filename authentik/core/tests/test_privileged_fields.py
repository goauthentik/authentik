"""Test PrivilegedFieldsSerializerMixin"""

from unittest.mock import patch

from rest_framework.test import APIRequestFactory, APITestCase

from authentik.core.api.utils import ModelSerializer as CustomModelSerializer
from authentik.core.api.utils import PrivilegedFieldsSerializerMixin
from authentik.core.models import Group
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.lib.generators import generate_id
from authentik.rbac.models import Role


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

    def test_get_privileged_fields_override(self):
        """to_representation consults get_privileged_fields(), not the attribute directly"""
        request = APIRequestFactory().get("/")
        request.user = create_test_user()
        with patch.object(GroupPrivilegedSerializer, "get_privileged_fields", return_value=[]):
            data = GroupPrivilegedSerializer(self.group, context={"request": request}).data
        self.assertEqual(data["attributes"], self.group.attributes)
