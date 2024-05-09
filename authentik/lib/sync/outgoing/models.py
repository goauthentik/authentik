from typing import Any, Self

from django.core.cache import cache
from django.db.models import Model, QuerySet, TextChoices
from redis.lock import Lock

from authentik.core.models import Group, User
from authentik.lib.sync.outgoing import PAGE_TIMEOUT
from authentik.lib.sync.outgoing.base import BaseOutgoingSyncClient


class OutgoingSyncDeleteAction(TextChoices):
    """Action taken when a user/group is deleted in authentik. Suspend is not available for groups,
    and will be treated as `do_nothing`"""

    DO_NOTHING = "do_nothing"
    DELETE = "delete"
    SUSPEND = "suspend"


class OutgoingSyncProvider(Model):

    class Meta:
        abstract = True

    def client_for_model[
        T: User | Group
    ](self, model: type[T]) -> BaseOutgoingSyncClient[T, Any, Any, Self]:
        raise NotImplementedError

    def get_object_qs[T: User | Group](self, type: type[T]) -> QuerySet[T]:
        raise NotImplementedError

    @property
    def sync_lock(self) -> Lock:
        """Redis lock to prevent multiple parallel syncs happening"""
        return Lock(
            cache.client.get_client(),
            name=f"goauthentik.io/providers/outgoing-sync/{str(self.pk)}",
            timeout=(60 * 60 * PAGE_TIMEOUT) * 3,
        )
