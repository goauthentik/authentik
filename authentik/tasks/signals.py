"""admin signals"""

import pglock
from django.dispatch import receiver
from django.utils.timezone import now, timedelta
from packaging.version import parse
from prometheus_client import Gauge

from authentik import get_full_version
from authentik.root.monitoring import monitoring_set
from authentik.tasks.models import WorkerStatus

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


_version = parse(get_full_version())


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
