import dramatiq
from dramatiq.broker import Broker, get_broker
from dramatiq.encoder import PickleEncoder

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikTasksConfig(ManagedAppConfig):
    name = "authentik.tasks"
    label = "authentik_tasks"
    verbose_name = "authentik Tasks"
    default = True

    def _set_dramatiq_middlewares(self, broker: Broker) -> None:
        from authentik.tasks.middleware import CurrentTask, FullyQualifiedActorName

        broker.add_middleware(FullyQualifiedActorName())
        # broker.add_middleware(Prometheus())
        broker.add_middleware(CurrentTask())

    def ready(self) -> None:
        from authentik.tasks.broker import PostgresBroker

        dramatiq.set_encoder(PickleEncoder())

        broker = PostgresBroker()
        self._set_dramatiq_middlewares(broker)
        dramatiq.set_broker(broker)

        return super().ready()

    def use_test_broker(self) -> None:
        from authentik.tasks.test import TestBroker

        old_broker = get_broker()
        broker = TestBroker()
        self._set_dramatiq_middlewares(broker)
        dramatiq.set_broker(broker)
        for actor_name in old_broker.get_declared_actors():
            actor = old_broker.get_actor(actor_name)
            actor.broker = broker
            actor.broker.declare_actor(actor)
