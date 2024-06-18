from collections.abc import Callable

from django.utils.text import slugify
from drf_spectacular.utils import OpenApiResponse, extend_schema
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.fields import BooleanField
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.events.api.tasks import SystemTaskSerializer
from authentik.lib.sync.outgoing.models import OutgoingSyncProvider


class SyncStatusSerializer(PassiveSerializer):
    """Provider sync status"""

    is_running = BooleanField(read_only=True)
    tasks = SystemTaskSerializer(many=True, read_only=True)


class OutgoingSyncProviderStatusMixin:
    """Common API Endpoints for Outgoing sync providers"""

    sync_single_task: Callable = None

    @extend_schema(
        responses={
            200: SyncStatusSerializer(),
            404: OpenApiResponse(description="Task not found"),
        }
    )
    @action(
        methods=["GET"],
        detail=True,
        pagination_class=None,
        url_path="sync/status",
        filter_backends=[],
    )
    def sync_status(self, request: Request, pk: int) -> Response:
        """Get provider's sync status"""
        provider: OutgoingSyncProvider = self.get_object()
        tasks = list(
            get_objects_for_user(request.user, "authentik_events.view_systemtask").filter(
                name=self.sync_single_task.__name__,
                uid=slugify(provider.name),
            )
        )
        with provider.sync_lock as lock_acquired:
            status = {
                "tasks": tasks,
                # If we could not acquire the lock, it means a task is using it, and thus is running
                "is_running": not lock_acquired,
            }
        return Response(SyncStatusSerializer(status).data)


class OutgoingSyncConnectionCreateMixin:
    """Mixin for connection objects that fetches remote data upon creation"""

    def perform_create(self, serializer: ModelSerializer):
        super().perform_create(serializer)
        try:
            instance = serializer.instance
            client = instance.provider.client_for_model(instance.__class__)
            client.update_single_attribute(instance)
            instance.save()
        except NotImplementedError:
            pass
