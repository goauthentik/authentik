import dramatiq
from dramatiq.encoder import PickleEncoder

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikTasksConfig(ManagedAppConfig):
    name = "authentik.tasks"
    label = "authentik_tasks"
    verbose_name = "authentik Tasks"
    default = True

    def ready(self) -> None:
        from authentik.tasks.broker import PostgresBroker
        from authentik.tasks.middleware import CurrentTask, FullyQualifiedActorName

        dramatiq.set_encoder(PickleEncoder())
        broker = PostgresBroker()
        broker.add_middleware(FullyQualifiedActorName())
        # broker.add_middleware(Prometheus())
        broker.add_middleware(CurrentTask())
        dramatiq.set_broker(broker)
        return super().ready()
