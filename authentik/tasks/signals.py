"""admin signals"""

from datetime import timedelta

import pglock
from django.db.models import Count
from django.dispatch import receiver
from django.utils.timezone import now
from django_dramatiq_postgres.models import TaskState
from packaging.version import parse
from prometheus_client import Gauge

from authentik import authentik_full_version
from authentik.root.monitoring import monitoring_set
from authentik.tasks.models import Task, WorkerStatus

OLD_GAUGE_WORKERS = Gauge(
    "authentik_admin_workers",
    "Currently connected workers, their versions and if they are the same version as authentik",
    ["version", "version_matched"],
)
GAUGE_WORKERS = Gauge(
    "authentik_tasks_workers",
    "Currently connected workers, their versions and if they are the same version as authentik",
    ["version", "version_matched"],
)
GAUGE_TASKS_QUEUED = Gauge(
    "authentik_tasks_queued",
    "The number of tasks in queue.",
    ["queue_name", "actor_name"],
)


_version = parse(authentik_full_version())


@receiver(monitoring_set)
def monitoring_set_workers(sender, **kwargs):
    """Set worker gauge"""
    worker_version_count = {}
    for status in WorkerStatus.objects.filter(last_seen__gt=now() - timedelta(minutes=2)):
        lock_id = f"goauthentik.io/worker/status/{status.pk}"
        with pglock.advisory(lock_id, timeout=0, side_effect=pglock.Return) as acquired:
            # The worker doesn't hold the lock, it isn't running
            if acquired:
                continue
            version_matching = parse(status.version) == _version
            worker_version_count.setdefault(
                status.version, {"count": 0, "matching": version_matching}
            )
            worker_version_count[status.version]["count"] += 1
    for version, stats in worker_version_count.items():
        OLD_GAUGE_WORKERS.labels(version, stats["matching"]).set(stats["count"])
        GAUGE_WORKERS.labels(version, stats["matching"]).set(stats["count"])


@receiver(monitoring_set)
def monitoring_set_queued_tasks(sender, **kwargs):
    """Set number of queued tasks"""
    for stats in Task.objects.values("queue_name", "actor_name").distinct():
        GAUGE_TASKS_QUEUED.labels(stats["queue_name"], stats["actor_name"]).set(0)
    for stats in (
        Task.objects.filter(state=TaskState.QUEUED)
        .values("queue_name", "actor_name")
        .annotate(count=Count("pk"))
    ):
        GAUGE_TASKS_QUEUED.labels(stats["queue_name"], stats["actor_name"]).set(stats["count"])
