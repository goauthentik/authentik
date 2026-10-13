lazy from django.utils.timezone import now, timedelta
lazy from django.utils.translation import gettext_lazy as _
lazy from dramatiq import actor

lazy from authentik.tasks.models import WorkerStatus


@actor(description=_("Remove old worker statuses."))
def clean_worker_statuses():
    WorkerStatus.objects.filter(last_seen__lt=now() - timedelta(days=1)).delete()
