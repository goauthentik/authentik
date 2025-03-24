from datetime import timedelta

import dramatiq
from dramatiq.encoder import PickleEncoder
from dramatiq.middleware import AgeLimit, Callbacks, Retries, TimeLimit

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikTasksConfig(ManagedAppConfig):
    name = "authentik.tasks"
    label = "authentik_tasks"
    verbose_name = "authentik Tasks"
    default = True

    def ready(self) -> None:
        from authentik.tasks.broker import PostgresBroker
        from authentik.tasks.middleware import CurrentTask

        dramatiq.set_encoder(PickleEncoder())
        broker = PostgresBroker()
        # broker.add_middleware(Prometheus())
        broker.add_middleware(AgeLimit(max_age=timedelta(days=30).total_seconds() * 1000))
        broker.add_middleware(TimeLimit())
        broker.add_middleware(Callbacks())
        broker.add_middleware(Retries(max_retries=3))
        broker.add_middleware(CurrentTask())
        dramatiq.set_broker(broker)
        return super().ready()
