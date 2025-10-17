from django.db.migrations.autodetector import MigrationAutodetector as BaseMigrationAutodetector
from pgtrigger.migrations import MigrationAutodetectorMixin

MigrationAutodetector = type(
    "MigrationAutodetector",
    (MigrationAutodetectorMixin, BaseMigrationAutodetector),
    {},
)
