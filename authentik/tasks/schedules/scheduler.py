import pglock
from django_dramatiq_postgres.scheduler import Scheduler as SchedulerBase
from structlog.stdlib import get_logger

from authentik.tenants.models import Tenant

LOGGER = get_logger()


class Scheduler(SchedulerBase):
    def _lock(self, tenant: Tenant) -> pglock.advisory:
        return pglock.advisory(
            lock_id=f"authentik.scheduler/{tenant.schema_name}",
            side_effect=pglock.Return,
            timeout=0,
        )

    def run(self):
        for tenant in Tenant.objects.filter(ready=True):
            with tenant:
                with self._lock(tenant) as lock_acquired:
                    if not lock_acquired:
                        self.logger.debug("Could not acquire lock, skipping scheduling")
                        return
                    count = self._run()
                    self.logger.info(f"Sent {count} scheduled tasks")
