"""Google provider signals"""

from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProvider
from authentik.enterprise.providers.google_workspace.tasks import (
    google_workspace_sync_direct,
    google_workspace_sync_m2m,
)
from authentik.lib.sync.outgoing.signals import register_signals

register_signals(
    GoogleWorkspaceProvider,
    task_sync_direct=google_workspace_sync_direct,
    task_sync_m2m=google_workspace_sync_m2m,
)
