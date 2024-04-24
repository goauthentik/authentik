from typing import Any, Self

from django.core.cache import cache
from django.db.models import Model, QuerySet
from redis.lock import Lock

from authentik.core.models import Group, User
from authentik.lib.sync.outgoing import PAGE_TIMEOUT
from authentik.lib.sync.outgoing.base import BaseOutgoingSyncClient


class OutgoingSyncProvider(Model):

    class Meta:
        abstract = True

    def client_for_model[
        T: User | Group
    ](self, model: type[T]) -> BaseOutgoingSyncClient[T, Any, Self]:
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
