"""Tenant-aware Celery beat scheduler"""

from tenant_schemas_celery.scheduler import (
    TenantAwarePersistentScheduler as BaseTenantAwarePersistentScheduler,
)
from tenant_schemas_celery.scheduler import TenantAwareScheduleEntry


class TenantAwarePersistentScheduler(BaseTenantAwarePersistentScheduler):
    """Tenant-aware Celery beat scheduler"""

    @classmethod
    def get_queryset(cls):
        return super().get_queryset().filter(ready=True)

    def apply_entry(self, entry: TenantAwareScheduleEntry, producer=None):
        # https://github.com/maciej-gol/tenant-schemas-celery/blob/master/tenant_schemas_celery/scheduler.py#L85
        # When (as by default) no tenant schemas are set, the public schema is excluded
        # so we need to explicitly include it here, otherwise the task is not executed
        if entry.tenant_schemas is None:
            entry.tenant_schemas = self.get_queryset().values_list("schema_name", flat=True)
        return super().apply_entry(entry, producer)
