"""Source API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.admin.forms.source import SOURCE_SERIALIZER_FIELDS
from passbook.sources.ldap.models import LDAPSource


class LDAPSourceSerializer(ModelSerializer):
    """LDAP Source Serializer"""

    class Meta:
        model = LDAPSource
        fields = SOURCE_SERIALIZER_FIELDS + [
            'server_uri',
            'bind_cn',
            'bind_password',
            'start_tls',
            'base_dn',
            'additional_user_dn',
            'additional_group_dn',
            'user_object_filter',
            'group_object_filter',
            'user_group_membership_field',
            'object_uniqueness_field',
            'sync_groups',
            'sync_parent_group',
            'property_mappings',
        ]
        extra_kwargs = {
            'password': {'bind_password': True}
        }


class LDAPSourceViewSet(ModelViewSet):
    """Source Viewset"""

    queryset = LDAPSource.objects.all()
    serializer_class = LDAPSourceSerializer
