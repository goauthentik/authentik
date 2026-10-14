from collections.abc import Iterable
from typing import TYPE_CHECKING

from django.db import transaction
from dramatiq.actor import Actor
from dramatiq.middleware import Middleware

from authentik.lib.sync.models import Sync

if TYPE_CHECKING:
    from dramatiq.broker import Broker, MessageProxy


class SyncMiddleware(Middleware):
    SyncModel: type[Sync]

    @staticmethod
    def sync_actors() -> Iterable[Actor]:
        return []

    def update_sync_status(self, message_id: str, actor_name: str):
        if all(actor_name != actor.actor_name for actor in self.sync_actors()):
            return

        with transaction.atomic():
            sync = self.SyncModel.objects.filter(tasks=message_id).first()
            if sync is None:
                return
            sync.persist_status()

    def after_ack(self, broker: Broker, message: MessageProxy) -> None:
        self.update_sync_status(str(message.message_id), message.actor_name)

    def after_nack(self, broker: Broker, message: MessageProxy) -> None:
        self.update_sync_status(str(message.message_id), message.actor_name)
