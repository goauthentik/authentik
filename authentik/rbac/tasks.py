"""authentik RBAC tasks"""

from django.utils.translation import gettext_lazy as _
from dramatiq import actor
from guardian.utils import clean_orphan_obj_perms

from authentik.tasks.middleware import CurrentTask

ORPHANED_PERMISSIONS_BATCH_SIZE = 1000
ORPHANED_PERMISSIONS_MAX_DURATION = 60 * 30


@actor(description=_("Remove object-level permissions whose object no longer exists."))
def clean_orphaned_object_permissions():
    self = CurrentTask.get_task()
    removed = clean_orphan_obj_perms(
        batch_size=ORPHANED_PERMISSIONS_BATCH_SIZE,
        max_duration_secs=ORPHANED_PERMISSIONS_MAX_DURATION,
    )
    self.info(f"Removed {removed} orphaned object permission(s)")
