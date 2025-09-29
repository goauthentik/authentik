"""admin signals"""

from django.dispatch import receiver
from packaging.version import parse
from prometheus_client import Gauge

from authentik import get_full_version
from authentik.root.celery import CELERY_APP
from authentik.root.monitoring import monitoring_set

GAUGE_WORKERS = Gauge(
    "authentik_admin_workers",
    "Currently connected workers, their versions and if they are the same version as authentik",
    ["version", "version_matched"],
)


_version = parse(get_full_version())


@receiver(monitoring_set)
def monitoring_set_workers(sender, **kwargs):
    """Set worker gauge"""
    raw: list[dict[str, dict]] = CELERY_APP.control.ping(timeout=0.5)
    worker_version_count = {}
    for worker in raw:
        key = list(worker.keys())[0]
        version = worker[key].get("version")
        version_matching = False
        if version:
            version_matching = parse(version) == _version
        worker_version_count.setdefault(version, {"count": 0, "matching": version_matching})
        worker_version_count[version]["count"] += 1
    for version, stats in worker_version_count.items():
        GAUGE_WORKERS.labels(version, stats["matching"]).set(stats["count"])
