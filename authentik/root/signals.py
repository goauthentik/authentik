from datetime import timedelta

from django.dispatch import Signal, receiver
from django.utils.timezone import now
from structlog.stdlib import get_logger

# Signal dispatched before actual startup trigger
pre_startup = Signal()
# Signal dispatched which should trigger all startup logic
startup = Signal()
# Signal dispatched after the startup logic
post_startup = Signal()

LOGGER = get_logger()


@receiver(pre_startup)
def pre_startup_log(sender, **_):
    sender._start_time = now()


@receiver(post_startup)
def post_startup_log(sender, **_):
    took: timedelta = now() - sender._start_time
    LOGGER.info("authentik Core Worker finished starting", took_s=took.total_seconds())
