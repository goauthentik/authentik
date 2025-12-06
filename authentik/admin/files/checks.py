from pathlib import Path

from django.core.checks import Warning, register

from authentik.lib.config import CONFIG


@register()
def check_root_media_does_not_exist(app_configs, **kwargs):
    """Check that /media doesn't exist"""
    if (
        CONFIG.get("storage.media.backend", CONFIG.get("storage.backend", "file")) == "file"
        and Path("/media").exists()
    ):
        return [
            Warning(
                "/media has been moved to /data/media.",
                hint="Check the release notes for migration steps.",
                id="ak.admin.files.E001",
            )
        ]
    return []
