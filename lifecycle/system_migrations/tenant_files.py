# flake8: noqa
from pathlib import Path

from lifecycle.migrate import BaseMigration

MEDIA_ROOT = Path(__file__).parent.parent.parent / "media"
TENANT_MEDIA_ROOT = MEDIA_ROOT / "public"


class Migration(BaseMigration):
    def needs_migration(self) -> bool:
        return not TENANT_MEDIA_ROOT.exists()

    def run(self):
        TENANT_MEDIA_ROOT.mkdir(parents=True)
        for d in ("application-icons", "source-icons", "flow-backgrounds"):
            if (MEDIA_ROOT / d).exists():
                (MEDIA_ROOT / d).rename(TENANT_MEDIA_ROOT / d)
