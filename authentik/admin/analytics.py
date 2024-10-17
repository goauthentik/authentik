"""authentik admin analytics"""

from typing import Any

from django.utils.translation import gettext_lazy as _

from authentik.root.celery import CELERY_APP


def get_analytics_description() -> dict[str, str]:
    return {
        "worker_count": _("Number of running workers"),
    }


def get_analytics_data() -> dict[str, Any]:
    worker_count = len(CELERY_APP.control.ping(timeout=0.5))
    return {
        "worker_count": worker_count,
    }
