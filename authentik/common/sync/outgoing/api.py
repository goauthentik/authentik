from celery import Task
from django.utils.text import slugify
from drf_spectacular.utils import OpenApiResponse, extend_schema
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.fields import BooleanField, CharField, ChoiceField
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.common.sync.outgoing.models import OutgoingSyncProvider
from authentik.common.utils.reflection import class_to_path
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.core.models import Group, User
from authentik.events.api.tasks import SystemTaskSerializer
from authentik.events.logs import LogEvent, LogEventSerializer
from authentik.rbac.filters import ObjectFilter


class SyncStatusSerializer(PassiveSerializer):
    """Provider sync status"""

    is_running = BooleanField(read_only=True)
    tasks = SystemTaskSerializer(many=True, read_only=True)


class SyncObjectSerializer(PassiveSerializer):
    """Sync object serializer"""

    sync_object_model = ChoiceField(
        choices=(
            (class_to_path(User), "user"),
            (class_to_path(Group), "group"),
        )
    )
    sync_object_id = CharField()
    override_dry_run = BooleanField(default=False)


class SyncObjectResultSerializer(PassiveSerializer):
    """Result of a single object sync"""

    messages = LogEventSerializer(many=True, read_only=True)


class OutgoingSyncProviderStatusMixin:
    """Common API Endpoints for Outgoing sync providers"""

    sync_single_task: type[Task] = None
    sync_objects_task: type[Task] = None

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
        filter_backends=[ObjectFilter],
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

    @extend_schema(
        request=SyncObjectSerializer,
        responses={200: SyncObjectResultSerializer()},
    )
    @action(
        methods=["POST"],
        detail=True,
        pagination_class=None,
        url_path="sync/object",
        filter_backends=[ObjectFilter],
    )
    def sync_object(self, request: Request, pk: int) -> Response:
        """Sync/Re-sync a single user/group object"""
        provider: OutgoingSyncProvider = self.get_object()
        params = SyncObjectSerializer(data=request.data)
        params.is_valid(raise_exception=True)
        res: list[LogEvent] = self.sync_objects_task.delay(
            params.validated_data["sync_object_model"],
            page=1,
            provider_pk=provider.pk,
            pk=params.validated_data["sync_object_id"],
            override_dry_run=params.validated_data["override_dry_run"],
        ).get()
        return Response(SyncObjectResultSerializer(instance={"messages": res}).data)


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
