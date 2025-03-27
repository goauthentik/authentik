from django.db import router, transaction
from structlog.stdlib import get_logger
from authentik.tasks.schedules.models import Schedule
from django.utils.timezone import now
from dramatiq.broker import Broker
import pickle

from authentik.tenants.models import Tenant
import pglock


LOGGER = get_logger()


class Scheduler:
    def __init__(self, broker: Broker):
        self.broker = broker

    def process_schedule(self, schedule: Schedule):
        next_run = schedule.next_run
        while True:
            next_run = schedule.calculate_next_run(next_run)
            if next_run > now():
                break
        schedule.next_run = next_run

        actor = self.broker.get_actor(schedule.actor_name)
        actor.send_with_options(
            args=pickle.loads(schedule.args),
            kwargs=pickle.loads(schedule.kwargs),
            options={
                "schedule_uid": schedule.uid,
            },
        )

        schedule.save()

    def run_per_tenant(self, tenant: Tenant):
        with pglock.advisory(
            lock_id=f"goauthentik.io/{tenant.schema_name}/tasks/scheduler",
            side_effect=pglock.Return,
            timeout=0,
        ) as lock_acquired:
            if not lock_acquired:
                LOGGER.debug(
                    "Failed to acquire lock for tasks scheduling, skipping",
                    tenant=tenant.schema_name,
                )
            with transaction.atomic(using=router.db_for_write(Schedule)):
                for schedule in Schedule.objects.select_for_update().filter(next_run__lt=now()):
                    self.process_schedule(schedule)

    def run(self):
        for tenant in Tenant.objects.filter(enabled=True):
            with tenant:
                self.run_per_tenant(tenant)
