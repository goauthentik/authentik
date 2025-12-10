from pathlib import Path

from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.config import CONFIG


class AuthentikFilesConfig(ManagedAppConfig):
    name = "authentik.admin.files"
    label = "authentik_admin_files"
    verbose_name = "authentik Files"
    default = True

    @ManagedAppConfig.reconcile_global
    def check_for_media_mount(self):
        from authentik.events.models import Event, EventAction

        if (
            CONFIG.get("storage.media.backend", CONFIG.get("storage.backend", "file")) == "file"
            and Path("/media").exists()
        ):
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message="/media has been moved to /data/media. "
                "Check the release notes for migration steps.",
            ).save()
