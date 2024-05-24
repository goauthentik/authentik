"""Reputation tasks"""

from django.core.cache import cache
from structlog.stdlib import get_logger

from authentik.events.context_processors.asn import ASN_CONTEXT_PROCESSOR
from authentik.events.context_processors.geoip import GEOIP_CONTEXT_PROCESSOR
from authentik.events.models import TaskStatus
from authentik.events.system_tasks import SystemTask, prefill_task
from authentik.policies.reputation.apps import CACHE_KEY_PREFIX
from authentik.policies.reputation.models import Reputation
from authentik.root.celery import CELERY_APP

LOGGER = get_logger()


@CELERY_APP.task(bind=True, base=SystemTask)
@prefill_task
def save_reputation(self: SystemTask):
    """Save currently cached reputation to database"""
    objects_to_update = []
    for _, score in cache.get_many(cache.keys(CACHE_KEY_PREFIX + "*")).items():
        rep, _ = Reputation.objects.get_or_create(
            ip=score["ip"],
            identifier=score["identifier"],
        )
        rep.ip_geo_data = GEOIP_CONTEXT_PROCESSOR.city_dict(score["ip"]) or {}
        rep.ip_asn_data = ASN_CONTEXT_PROCESSOR.asn_dict(score["ip"]) or {}
        rep.score = score["score"]
        objects_to_update.append(rep)
    Reputation.objects.bulk_update(objects_to_update, ["score", "ip_geo_data"])
    self.set_status(TaskStatus.SUCCESSFUL, "Successfully updated Reputation")
