"""admin signals"""

from datetime import timedelta

from django.db.models import Count
from django.dispatch import receiver
from django.utils.timezone import now
from django_dramatiq_postgres.models import TaskState
from dramatiq.broker import get_broker
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


@receiver(monitoring_set)
def monitoring_set_workers(sender, **kwargs):
    """Set worker gauge"""
    worker_version_count = {}
    our_version = parse(authentik_full_version())
    for status in WorkerStatus.objects.filter(last_seen__gt=now() - timedelta(seconds=45)):
        version_matching = parse(status.version) == our_version
        worker_version_count.setdefault(status.version, {"count": 0, "matching": version_matching})
        worker_version_count[status.version]["count"] += 1
    for version, stats in worker_version_count.items():
        OLD_GAUGE_WORKERS.labels(version, stats["matching"]).set(stats["count"])
        GAUGE_WORKERS.labels(version, stats["matching"]).set(stats["count"])


@receiver(monitoring_set)
def monitoring_set_queued_tasks(sender, **kwargs):
    """Set the queued-tasks gauge for every registered actor.

    Enumerates ``(queue_name, actor_name)`` combinations from the dramatiq
    broker's in-memory actor registry rather than via
    ``SELECT DISTINCT ... FROM authentik_tasks_task`` — the latter forces a
    full-table scan on every Prometheus scrape and becomes a top CPU consumer
    under sustained load as the task table grows.
    """
    broker = get_broker()
    for actor in broker.actors.values():
        GAUGE_TASKS_QUEUED.labels(actor.queue_name, actor.actor_name).set(0)
    for stats in (
        Task.objects.filter(state=TaskState.QUEUED)
        .values("queue_name", "actor_name")
        .annotate(count=Count("pk"))
    ):
        GAUGE_TASKS_QUEUED.labels(stats["queue_name"], stats["actor_name"]).set(stats["count"])
