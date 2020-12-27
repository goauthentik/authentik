"""Source API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.admin.forms.source import SOURCE_SERIALIZER_FIELDS
from authentik.core.api.utils import MetaNameSerializer
from authentik.sources.ldap.models import LDAPPropertyMapping, LDAPSource


class LDAPSourceSerializer(ModelSerializer, MetaNameSerializer):
    """LDAP Source Serializer"""

    class Meta:
        model = LDAPSource
        fields = SOURCE_SERIALIZER_FIELDS + [
            "server_uri",
            "bind_cn",
            "bind_password",
            "start_tls",
            "base_dn",
            "additional_user_dn",
            "additional_group_dn",
            "user_object_filter",
            "group_object_filter",
            "user_group_membership_field",
            "object_uniqueness_field",
            "sync_users",
            "sync_users_password",
            "sync_groups",
            "sync_parent_group",
            "property_mappings",
        ]
        extra_kwargs = {"bind_password": {"write_only": True}}


class LDAPPropertyMappingSerializer(ModelSerializer):
    """LDAP PropertyMapping Serializer"""

    class Meta:
        model = LDAPPropertyMapping
        fields = ["pk", "name", "expression", "object_field"]


class LDAPSourceViewSet(ModelViewSet):
    """LDAP Source Viewset"""

    queryset = LDAPSource.objects.all()
    serializer_class = LDAPSourceSerializer


class LDAPPropertyMappingViewSet(ModelViewSet):
    """LDAP PropertyMapping Viewset"""

    queryset = LDAPPropertyMapping.objects.all()
    serializer_class = LDAPPropertyMappingSerializer
