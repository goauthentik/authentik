from tenant_schemas_celery.scheduler import (
    TenantAwarePersistentScheduler as BaseTenantAwarePersistentScheduler,
)


class TenantAwarePersistentScheduler(BaseTenantAwarePersistentScheduler):
    @classmethod
    def get_queryset(cls):
        return super().get_queryset().filter(ready=True)
