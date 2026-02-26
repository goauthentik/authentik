from typing import Any, Self

import pglock
from django.core.paginator import Paginator
from django.core.validators import MinValueValidator
from django.db import connection, models
from django.db.models import Model, QuerySet, TextChoices
from django.utils.translation import gettext_lazy as _
from dramatiq.actor import Actor

from authentik.core.models import Group, User
from authentik.lib.sync.outgoing.base import BaseOutgoingSyncClient
from authentik.lib.utils.time import fqdn_rand, timedelta_from_string, timedelta_string_validator
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

    sync_page_size = models.PositiveIntegerField(
        help_text=_("Controls the number of objects synced in a single task"),
        default=100,
        validators=[MinValueValidator(1)],
    )
    sync_page_timeout = models.TextField(
        help_text=_("Timeout for synchronization of a single page"),
        default="minutes=30",
        validators=[timedelta_string_validator],
    )

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

    def get_object_qs[T: User | Group](self, type: type[T], **kwargs) -> QuerySet[T]:
        raise NotImplementedError

    @classmethod
    def get_object_mappings(cls, obj: User | Group) -> list[tuple[str, str]]:
        """
        Get a list of mapping between User/Group and ProviderUser/Group:
        [("provider_pk", "obj_pk")]
        """
        raise NotImplementedError

    def get_paginator[T: User | Group](self, type: type[T]) -> Paginator:
        return Paginator(self.get_object_qs(type), self.sync_page_size)

    def get_object_sync_time_limit_ms[T: User | Group](self, type: type[T]) -> int:
        num_pages: int = self.get_paginator(type).num_pages
        page_timeout_ms = timedelta_from_string(self.sync_page_timeout).total_seconds() * 1000
        return int(num_pages * page_timeout_ms * 1.5)

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

    def sync_dispatch(self) -> None:
        for schedule in self.schedules.all():
            schedule.send()

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
