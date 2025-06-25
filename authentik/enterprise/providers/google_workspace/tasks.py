"""Google Provider tasks"""

from django.utils.translation import gettext_lazy as _
from dramatiq.actor import actor

from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProvider
from authentik.lib.sync.outgoing.tasks import SyncTasks

sync_tasks = SyncTasks(GoogleWorkspaceProvider)


@actor(description=_("Sync Google Workspace provider objects."))
def google_workspace_sync_objects(*args, **kwargs):
    return sync_tasks.sync_objects(*args, **kwargs)


@actor(description=_("Full sync for Google Workspace provider."))
def google_workspace_sync(provider_pk: int, *args, **kwargs):
    """Run full sync for Google Workspace provider"""
    return sync_tasks.sync(provider_pk, google_workspace_sync_objects)


@actor(description=_("Sync a direct object (user, group) for Google Workspace provider."))
def google_workspace_sync_direct(*args, **kwargs):
    return sync_tasks.sync_signal_direct(*args, **kwargs)


@actor(
    description=_(
        "Dispatch syncs for a direct object (user, group) for Google Workspace providers."
    )
)
def google_workspace_sync_direct_dispatch(*args, **kwargs):
    return sync_tasks.sync_signal_direct_dispatch(google_workspace_sync_direct, *args, **kwargs)


@actor(description=_("Sync a related object (memberships) for Google Workspace provider."))
def google_workspace_sync_m2m(*args, **kwargs):
    return sync_tasks.sync_signal_m2m(*args, **kwargs)


@actor(
    description=_(
        "Dispatch syncs for a related object (memberships) for Google Workspace providers."
    )
)
def google_workspace_sync_m2m_dispatch(*args, **kwargs):
    return sync_tasks.sync_signal_m2m_dispatch(google_workspace_sync_m2m, *args, **kwargs)
