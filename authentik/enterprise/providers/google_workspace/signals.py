"""Google provider signals"""

from authentik.common.sync.outgoing.signals import register_signals
from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProvider
from authentik.enterprise.providers.google_workspace.tasks import (
    google_workspace_sync,
    google_workspace_sync_direct,
    google_workspace_sync_m2m,
)

register_signals(
    GoogleWorkspaceProvider,
    task_sync_single=google_workspace_sync,
    task_sync_direct=google_workspace_sync_direct,
    task_sync_m2m=google_workspace_sync_m2m,
)
