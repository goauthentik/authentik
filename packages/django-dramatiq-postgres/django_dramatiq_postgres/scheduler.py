from typing import Any, cast

import pglock
from django.db import router, transaction
from django.db.models import QuerySet
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from django.utils.timezone import now
from dramatiq.broker import Broker
from structlog.stdlib import get_logger

from django_dramatiq_postgres.conf import Conf
from django_dramatiq_postgres.models import ScheduleBase


class Scheduler:
    broker: Broker

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.logger = get_logger(__name__, type(self))

    @cached_property
    def model(self) -> type[ScheduleBase]:
        schedule_model = cast(str, Conf().schedule_model)
        model: type[ScheduleBase] = import_string(schedule_model)
        return model

    @property
    def query_set(self) -> QuerySet[ScheduleBase]:
        return self.model._default_manager.filter(paused=False)

    def process_schedule(self, schedule: ScheduleBase) -> None:
        schedule.next_run = schedule.compute_next_run()
        schedule.send(self.broker)
        schedule.save()

    def _lock(self) -> pglock.advisory:
        return pglock.advisory(
            lock_id=f"{Conf().channel_prefix}.scheduler",
            side_effect=pglock.Return,
            timeout=0,
        )

    def _run(self) -> int:
        count = 0
        with transaction.atomic(using=router.db_for_write(self.model)):
            for schedule in self.query_set.select_for_update().filter(
                next_run__lt=now(),
            ):
                self.process_schedule(schedule)
                count += 1
        return count

    def run(self) -> int:
        with self._lock() as lock_acquired:
            if not lock_acquired:
                self.logger.debug("Could not acquire lock, skipping scheduling")
                return -1
            count = self._run()
            self.logger.info("Sent scheduled tasks", count=count)
        return count
