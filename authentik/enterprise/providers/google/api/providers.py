"""Google Provider API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.providers.google.models import GoogleProvider


class GoogleProviderSerializer(EnterpriseRequiredMixin, ProviderSerializer):
    """GoogleProvider Serializer"""

    class Meta:
        model = GoogleProvider
        fields = [
            "pk",
            "name",
            "property_mappings",
            # "property_mappings_group",
            "component",
            "assigned_backchannel_application_slug",
            "assigned_backchannel_application_name",
            "verbose_name",
            "verbose_name_plural",
            "meta_model_name",
            "delegated_subject",
            "credentials",
            "scopes",
            "exclude_users_service_account",
            "filter_group",
        ]
        extra_kwargs = {}


class GoogleProviderViewSet(UsedByMixin, ModelViewSet):
    """GoogleProvider Viewset"""

    queryset = GoogleProvider.objects.all()
    serializer_class = GoogleProviderSerializer
    filterset_fields = [
        "name",
        "exclude_users_service_account",
        "delegated_subject",
        "filter_group",
    ]
    search_fields = ["name"]
    ordering = ["name"]

    # @extend_schema(
    #     responses={
    #         200: SCIMSyncStatusSerializer(),
    #         404: OpenApiResponse(description="Task not found"),
    #     }
    # )
    # @action(methods=["GET"], detail=True, pagination_class=None, filter_backends=[])
    # def sync_status(self, request: Request, pk: int) -> Response:
    #     """Get provider's sync status"""
    #     provider: GoogleProvider = self.get_object()
    #     tasks = list(
    #         get_objects_for_user(request.user, "authentik_events.view_systemtask").filter(
    #             name="scim_sync",
    #             uid=slugify(provider.name),
    #         )
    #     )
    #     status = {
    #         "tasks": tasks,
    #         "is_running": provider.sync_lock.locked(),
    #     }
    #     return Response(SCIMSyncStatusSerializer(status).data)
