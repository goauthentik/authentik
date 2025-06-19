import pglock
from django.db import router, transaction
from django.db.models import QuerySet
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from django.utils.timezone import now
from dramatiq.broker import Broker
from dramatiq.logging import get_logger

from django_dramatiq_postgres.conf import Conf
from django_dramatiq_postgres.models import ScheduleBase


class Scheduler:
    def __init__(self, broker: Broker):
        self.logger = get_logger(__name__, type(self))
        self.broker = broker

    @cached_property
    def model(self) -> type[ScheduleBase]:
        return import_string(Conf().task_class)

    @property
    def query_set(self) -> QuerySet:
        return self.model.objects.filter(paused=False)

    def process_schedule(self, schedule: ScheduleBase):
        schedule.next_run = schedule.compute_next_run()
        schedule.send(self.broker)
        schedule.save()

    def _lock(self) -> pglock.advisory:
        return pglock.advisory(
            lock_id=f"{Conf().channel_prefix}.scheduler",
            side_effect=pglock.Return,
            timeout=0,
        )

    def _run(self):
        with transaction.atomic(using=router.db_for_write(self.model)):
            for schedule in self.query_set.select_for_update().filter(
                next_run__lt=now(),
            ):
                self.process_schedule(schedule)

    def run(self):
        with self._lock() as lock_acquired:
            if not lock_acquired:
                return
            self._run()
