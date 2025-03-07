"""Google provider signals"""

from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProvider
from authentik.lib.sync.outgoing.signals import register_signals

register_signals(
    GoogleWorkspaceProvider,
    task_sync_single="authentik.enterprise.providers.google_workspace.tasks.google_workspace_sync",
    task_sync_direct="authentik.enterprise.providers.google_workspace.tasks.google_workspace_direct",
    task_sync_m2m="authentik.enterprise.providers.google_workspace.tasks.google_workspace_m2m",
)
