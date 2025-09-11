from typing import Any, Self

import pglock
from django.core.paginator import Paginator
from django.db import connection, models
from django.db.models import Model, QuerySet, TextChoices
from django.utils.translation import gettext_lazy as _
from dramatiq.actor import Actor

from authentik.core.models import Group, User
from authentik.lib.sync.outgoing import PAGE_SIZE, PAGE_TIMEOUT_MS
from authentik.lib.sync.outgoing.base import BaseOutgoingSyncClient
from authentik.lib.utils.time import fqdn_rand
from authentik.tasks.schedules.common import ScheduleSpec
from authentik.tasks.schedules.models import ScheduledModel


class OutgoingSyncDeleteAction(TextChoices):
    """Action taken when a user/group is deleted in authentik. Suspend is not available for groups,
    and will be treated as `do_nothing`"""

    DO_NOTHING = "do_nothing"
    DELETE = "delete"
    SUSPEND = "suspend"


class OutgoingSyncProvider(ScheduledModel, Model):
    """Base abstract models for providers implementing outgoing sync"""

    dry_run = models.BooleanField(
        default=False,
        help_text=_(
            "When enabled, provider will not modify or create objects in the remote system."
        ),
    )

    class Meta:
        abstract = True

    def client_for_model[T: User | Group](
        self, model: type[T]
    ) -> BaseOutgoingSyncClient[T, Any, Any, Self]:
        raise NotImplementedError

    def get_object_qs[T: User | Group](self, type: type[T]) -> QuerySet[T]:
        raise NotImplementedError

    def get_paginator[T: User | Group](self, type: type[T]) -> Paginator:
        return Paginator(self.get_object_qs(type), PAGE_SIZE)

    def get_object_sync_time_limit_ms[T: User | Group](self, type: type[T]) -> int:
        num_pages: int = self.get_paginator(type).num_pages
        return int(num_pages * PAGE_TIMEOUT_MS * 1.5)

    def get_sync_time_limit_ms(self) -> int:
        return int(
            (self.get_object_sync_time_limit_ms(User) + self.get_object_sync_time_limit_ms(Group))
            * 1.5
        )

    @property
    def sync_lock(self) -> pglock.advisory:
        """Postgres lock for syncing to prevent multiple parallel syncs happening"""
        return pglock.advisory(
            lock_id=f"goauthentik.io/{connection.schema_name}/providers/outgoing-sync/{str(self.pk)}",
            timeout=0,
            side_effect=pglock.Return,
        )

    @property
    def sync_actor(self) -> Actor:
        raise NotImplementedError

    @property
    def schedule_specs(self) -> list[ScheduleSpec]:
        return [
            ScheduleSpec(
                actor=self.sync_actor,
                uid=self.name,
                args=(self.pk,),
                options={
                    "time_limit": self.get_sync_time_limit_ms(),
                },
                send_on_save=True,
                crontab=f"{fqdn_rand(self.pk)} */4 * * *",
            ),
        ]
