"""Source API Views"""
from django.http.response import Http404
from django.utils.text import slugify
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.admin.api.tasks import TaskSerializer
from authentik.core.api.propertymappings import PropertyMappingSerializer
from authentik.core.api.sources import SourceSerializer
from authentik.events.monitored_tasks import TaskInfo
from authentik.sources.ldap.models import LDAPPropertyMapping, LDAPSource


class LDAPSourceSerializer(SourceSerializer):
    """LDAP Source Serializer"""

    class Meta:
        model = LDAPSource
        fields = SourceSerializer.Meta.fields + [
            "server_uri",
            "bind_cn",
            "bind_password",
            "start_tls",
            "base_dn",
            "additional_user_dn",
            "additional_group_dn",
            "user_object_filter",
            "group_object_filter",
            "group_membership_field",
            "object_uniqueness_field",
            "sync_users",
            "sync_users_password",
            "sync_groups",
            "sync_parent_group",
            "property_mappings",
            "property_mappings_group",
        ]
        extra_kwargs = {"bind_password": {"write_only": True}}


class LDAPSourceViewSet(ModelViewSet):
    """LDAP Source Viewset"""

    queryset = LDAPSource.objects.all()
    serializer_class = LDAPSourceSerializer
    lookup_field = "slug"

    @swagger_auto_schema(
        responses={200: TaskSerializer(many=False), 404: "Task not found"}
    )
    @action(methods=["GET"], detail=True)
    # pylint: disable=unused-argument
    def sync_status(self, request: Request, slug: str) -> Response:
        """Get source's sync status"""
        source = self.get_object()
        task = TaskInfo.by_name(f"ldap_sync_{slugify(source.name)}")
        if not task:
            raise Http404
        return Response(TaskSerializer(task, many=False).data)


class LDAPPropertyMappingSerializer(PropertyMappingSerializer):
    """LDAP PropertyMapping Serializer"""

    class Meta:
        model = LDAPPropertyMapping
        fields = PropertyMappingSerializer.Meta.fields + [
            "object_field",
        ]


class LDAPPropertyMappingViewSet(ModelViewSet):
    """LDAP PropertyMapping Viewset"""

    queryset = LDAPPropertyMapping.objects.all()
    serializer_class = LDAPPropertyMappingSerializer
