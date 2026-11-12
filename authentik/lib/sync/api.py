from datetime import datetime
from typing import NotRequired, Protocol, TypedDict

import pglock
from django.db.models import Manager
from rest_framework.fields import BooleanField, ChoiceField, DateTimeField
from rest_framework.response import Response

from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.lib.sync.models import Sync
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


class SyncStatusTarget(Protocol):
    """Model with an advisory sync lock and schedules attached to it."""

    @property
    def sync_lock(self) -> pglock.advisory:
        pass

    schedules: Manager[Schedule]


def sync_status_response(target: SyncStatusTarget, actor_name: str) -> Response:
    """Status of the schedule that runs `actor_name` for `target`."""
    with target.sync_lock as lock_acquired:
        # If we could not acquire the lock, a task holds it and a sync is running.
        status: SyncStatusData = {"is_running": not lock_acquired}

    sync_schedule: Schedule | None = None
    for schedule in target.schedules.all():
        if schedule.actor_name == actor_name:
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
