"""SCIM provider signals"""

from authentik.enterprise.providers.google.models import GoogleProvider
from authentik.enterprise.providers.google.tasks import (
    google_sync,
    google_sync_direct,
    google_sync_m2m,
)
from authentik.lib.sync.outgoing.signals import register_signals

register_signals(
    GoogleProvider,
    task_sync_single=google_sync,
    task_sync_direct=google_sync_direct,
    task_sync_m2m=google_sync_m2m,
)
