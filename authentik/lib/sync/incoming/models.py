from django.db import models
from django.utils.translation import gettext_lazy as _

from authentik.core.models import Source
from authentik.tasks.schedules.models import ScheduledModel


class SyncOutgoingTriggerMode(models.TextChoices):
    # Do not trigger outgoing syncs
    NONE = "none"
    # Trigger immediately after object changed
    IMMEDIATE = "immediate"
    # Trigger at the end of full sync
    DEFERRED_END = "deferred_end"


class IncomingSyncSource(ScheduledModel, Source):
    sync_outgoing_trigger_mode = models.TextField(
        choices=SyncOutgoingTriggerMode.choices,
        default=SyncOutgoingTriggerMode.DEFERRED_END,
        help_text=_("When to trigger sync for outgoing providers"),
    )

    class Meta:
        abstract = True
