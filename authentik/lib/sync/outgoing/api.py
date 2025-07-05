from dramatiq.actor import Actor
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.fields import BooleanField, CharField, ChoiceField
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.core.models import Group, User
from authentik.events.logs import LogEventSerializer
from authentik.lib.sync.api import SyncStatusSerializer
from authentik.lib.sync.outgoing.models import OutgoingSyncProvider
from authentik.lib.utils.reflection import class_to_path
from authentik.rbac.filters import ObjectFilter
from authentik.tasks.models import Task, TaskStatus


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

    sync_task: Actor
    sync_objects_task: Actor

    @extend_schema(responses={200: SyncStatusSerializer()})
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

        status = {}

        with provider.sync_lock as lock_acquired:
            # If we could not acquire the lock, it means a task is using it, and thus is running
            status["is_running"] = not lock_acquired

        sync_schedule = None
        for schedule in provider.schedules.all():
            if schedule.actor_name == self.sync_task.actor_name:
                sync_schedule = schedule

        if not sync_schedule:
            return Response(SyncStatusSerializer(status).data)

        last_task: Task = (
            sync_schedule.tasks.exclude(
                aggregated_status__in=(TaskStatus.CONSUMED, TaskStatus.QUEUED)
            )
            .order_by("-mtime")
            .first()
        )
        last_successful_task: Task = (
            sync_schedule.tasks.filter(aggregated_status__in=(TaskStatus.DONE, TaskStatus.INFO))
            .order_by("-mtime")
            .first()
        )

        if last_task:
            status["last_sync_status"] = last_task.aggregated_status
        if last_successful_task:
            status["last_successful_sync"] = last_successful_task.mtime

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
        msg = self.sync_objects_task.send_with_options(
            kwargs={
                "object_type": params.validated_data["sync_object_model"],
                "page": 1,
                "provider_pk": provider.pk,
                "override_dry_run": params.validated_data["override_dry_run"],
                "pk": params.validated_data["sync_object_id"],
            },
            rel_obj=provider,
        )
        msg.get_result(block=True)
        task: Task = msg.options["task"]
        task.refresh_from_db()
        return Response(SyncObjectResultSerializer(instance={"messages": task._messages}).data)


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
