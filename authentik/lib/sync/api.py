from datetime import datetime
from typing import NotRequired, TypedDict

from dramatiq.actor import Actor
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.fields import BooleanField, ChoiceField, DateTimeField
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.lib.sync.models import Sync
from authentik.rbac.filters import ObjectFilter
from authentik.tasks.models import Task, TaskStatus
from authentik.tasks.schedules.models import Schedule


class SyncStatusSerializer(PassiveSerializer):
    """Provider/source sync status"""

    is_running = BooleanField()
    last_successful_sync = DateTimeField(required=False)
    last_sync_status = ChoiceField(required=False, choices=TaskStatus.choices)


class SyncStatusData(TypedDict):
    is_running: bool
    last_successful_sync: NotRequired[datetime]
    last_sync_status: NotRequired[str]


class SyncStatusMixin:
    """Mixin to add a sync status endpoint"""

    sync_task: Actor

    @extend_schema(responses={200: SyncStatusSerializer()})
    @action(
        methods=["GET"],
        detail=True,
        pagination_class=None,
        url_path="sync/status",
        filter_backends=[ObjectFilter],
    )
    def sync_status(self, request: Request, *args, **kwargs) -> Response:
        """Get provider's sync status"""
        target = self.get_object()
        with target.sync_lock as lock_acquired:
            # If we could not acquire the lock, a task holds it and a sync is running.
            status: SyncStatusData = {"is_running": not lock_acquired}

        sync_schedule: Schedule | None = None
        for schedule in target.schedules.all():
            if schedule.actor_name == self.sync_task.actor_name:
                sync_schedule = schedule

        if sync_schedule is None:
            return Response(SyncStatusSerializer(status).data)

        last_task: Task | None = (
            sync_schedule.tasks.filter(state__in=(TaskStatus.DONE, TaskStatus.REJECTED))
            .order_by("-mtime")
            .first()
        )
        last_successful_task: Task | None = (
            sync_schedule.tasks.filter(aggregated_status__in=(TaskStatus.DONE, TaskStatus.INFO))
            .order_by("-mtime")
            .first()
        )

        if last_task is not None:
            status["last_sync_status"] = last_task.aggregated_status
        if last_successful_task is not None:
            status["last_successful_sync"] = last_successful_task.mtime

        return Response(SyncStatusSerializer(status).data)


class SyncSerializer(ModelSerializer):
    class Meta:
        model = Sync
        fields = [
            "pk",
            "tasks",
            "started_at",
            "finished_at",
            "status",
        ]
