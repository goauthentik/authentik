"""SCIM Provider API Views"""
from django.utils.text import slugify
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.admin.api.tasks import TaskSerializer
from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.events.monitored_tasks import TaskInfo
from authentik.providers.scim.models import SCIMProvider


class SCIMProviderSerializer(ProviderSerializer):
    """SCIMProvider Serializer"""

    class Meta:
        model = SCIMProvider
        fields = [
            "pk",
            "name",
            "property_mappings",
            "property_mappings_group",
            "component",
            "assigned_backchannel_application_slug",
            "assigned_backchannel_application_name",
            "verbose_name",
            "verbose_name_plural",
            "meta_model_name",
            "url",
            "token",
            "exclude_users_service_account",
            "filter_group",
        ]
        extra_kwargs = {}


class SCIMProviderViewSet(UsedByMixin, ModelViewSet):
    """SCIMProvider Viewset"""

    queryset = SCIMProvider.objects.all()
    serializer_class = SCIMProviderSerializer
    filterset_fields = ["name", "exclude_users_service_account", "url", "filter_group"]
    search_fields = ["name", "url"]
    ordering = ["name", "url"]

    @extend_schema(
        responses={
            200: TaskSerializer(),
            404: OpenApiResponse(description="Task not found"),
        }
    )
    @action(methods=["GET"], detail=True, pagination_class=None, filter_backends=[])
    def sync_status(self, request: Request, pk: int) -> Response:
        """Get provider's sync status"""
        provider = self.get_object()
        task = TaskInfo.by_name(f"scim_sync:{slugify(provider.name)}")
        if not task:
            return Response(status=404)
        return Response(TaskSerializer(task).data)
