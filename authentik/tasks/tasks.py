from datetime import timedelta

from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from dramatiq import actor

from authentik.tasks.models import WorkerStatus


@actor(description=_("Remove old worker statuses."))
def clean_worker_statuses():
    WorkerStatus.objects.filter(last_seen__lt=now() - timedelta(days=1)).delete()
