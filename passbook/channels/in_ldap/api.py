"""Inlet API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.admin.forms.inlet import INLET_SERIALIZER_FIELDS
from passbook.channels.in_ldap.models import LDAPInlet, LDAPPropertyMapping


class LDAPInletSerializer(ModelSerializer):
    """LDAP Inlet Serializer"""

    class Meta:
        model = LDAPInlet
        fields = INLET_SERIALIZER_FIELDS + [
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


class LDAPInletViewSet(ModelViewSet):
    """LDAP Inlet Viewset"""

    queryset = LDAPInlet.objects.all()
    serializer_class = LDAPInletSerializer


class LDAPPropertyMappingViewSet(ModelViewSet):
    """LDAP PropertyMapping Viewset"""

    queryset = LDAPPropertyMapping.objects.all()
    serializer_class = LDAPPropertyMappingSerializer
