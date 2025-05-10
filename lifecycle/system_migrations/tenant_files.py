# flake8: noqa
from pathlib import Path

from authentik.common.config import CONFIG
from lifecycle.migrate import BaseMigration

MEDIA_ROOT = Path(__file__).parent.parent.parent / "media"
TENANT_MEDIA_ROOT = MEDIA_ROOT / "public"


class Migration(BaseMigration):
    def needs_migration(self) -> bool:
        return (
            not TENANT_MEDIA_ROOT.exists() and CONFIG.get("storage.media.backend", "file") != "s3"
        )

    def run(self):
        TENANT_MEDIA_ROOT.mkdir(parents=True)
        for d in ("application-icons", "source-icons", "flow-backgrounds"):
            if (MEDIA_ROOT / d).exists():
                (MEDIA_ROOT / d).rename(TENANT_MEDIA_ROOT / d)
