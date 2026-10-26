import pglock
from django.db import connection
from django_dramatiq_postgres.scheduler import Scheduler as SchedulerBase


class Scheduler(SchedulerBase):
    def _lock(self) -> pglock.advisory:
        return pglock.advisory(
            lock_id=f"authentik.scheduler/{connection.schema_name}",
            side_effect=pglock.Return,
            timeout=0,
            using=self.direct_db_alias,
        )
