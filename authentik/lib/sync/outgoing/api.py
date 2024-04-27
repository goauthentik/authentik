from django.utils.text import slugify
from drf_spectacular.utils import OpenApiResponse, extend_schema
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.fields import BooleanField
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.core.api.utils import PassiveSerializer
from authentik.events.api.tasks import SystemTaskSerializer
from authentik.lib.sync.outgoing.models import OutgoingSyncProvider


class SyncStatusSerializer(PassiveSerializer):
    """Provider sync status"""

    is_running = BooleanField(read_only=True)
    tasks = SystemTaskSerializer(many=True, read_only=True)


class OutgoingSyncProviderStatusMixin:

    @extend_schema(
        responses={
            200: SyncStatusSerializer(),
            404: OpenApiResponse(description="Task not found"),
        }
    )
    @action(methods=["GET"], detail=True, pagination_class=None, filter_backends=[])
    def sync_status(self, request: Request, pk: int) -> Response:
        """Get provider's sync status"""
        provider: OutgoingSyncProvider = self.get_object()
        tasks = list(
            get_objects_for_user(request.user, "authentik_events.view_systemtask").filter(
                # TODO: lookup correct task somehow
                name="scim_sync",
                uid=slugify(provider.name),
            )
        )
        status = {
            "tasks": tasks,
            "is_running": provider.sync_lock.locked(),
        }
        return Response(SyncStatusSerializer(status).data)
