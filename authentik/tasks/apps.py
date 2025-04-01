import dramatiq
from dramatiq.broker import Broker, get_broker
from dramatiq.encoder import PickleEncoder
from dramatiq.middleware import (
    AgeLimit,
    Callbacks,
    Pipelines,
    # Prometheus,
    Retries,
    ShutdownNotifications,
    TimeLimit,
)
from dramatiq.results.middleware import Results

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikTasksConfig(ManagedAppConfig):
    name = "authentik.tasks"
    label = "authentik_tasks"
    verbose_name = "authentik Tasks"
    default = True

    def _set_dramatiq_middlewares(self, broker: Broker, max_retries: int = 20) -> None:
        from authentik.tasks.middleware import CurrentTask, FullyQualifiedActorName
        from authentik.tasks.results import PostgresBackend

        # TODO: fixme
        # broker.add_middleware(Prometheus())
        broker.add_middleware(AgeLimit())
        # Task timeout, 5 minutes by default for all tasks
        broker.add_middleware(TimeLimit(time_limit=600 * 1000))
        broker.add_middleware(ShutdownNotifications())
        broker.add_middleware(Callbacks())
        broker.add_middleware(Pipelines())
        broker.add_middleware(Retries(max_retries=max_retries))
        broker.add_middleware(Results(backend=PostgresBackend(), store_results=True))
        broker.add_middleware(FullyQualifiedActorName())
        broker.add_middleware(CurrentTask())

    def ready(self) -> None:
        from authentik.tasks.broker import PostgresBroker

        dramatiq.set_encoder(PickleEncoder())

        broker = PostgresBroker(middleware=[])
        self._set_dramatiq_middlewares(broker)
        dramatiq.set_broker(broker)

        return super().ready()

    def use_test_broker(self) -> None:
        from authentik.tasks.test import TestBroker

        old_broker = get_broker()
        broker = TestBroker(middleware=[])
        self._set_dramatiq_middlewares(broker, max_retries=0)
        dramatiq.set_broker(broker)
        for actor_name in old_broker.get_declared_actors():
            actor = old_broker.get_actor(actor_name)
            actor.broker = broker
            actor.broker.declare_actor(actor)
