from datetime import timedelta
import dramatiq
from dramatiq.middleware import AgeLimit, Callbacks, Prometheus, Retries, TimeLimit
from authentik.blueprints.apps import ManagedAppConfig
from authentik.tasks.encoder import JSONPickleEncoder


class AuthentikTasksConfig(ManagedAppConfig):
    name = "authentik.tasks"
    label = "authentik_tasks"
    verbose_name = "authentik Tasks"
    default = True

    def ready(self) -> None:
        from authentik.tasks.broker import PostgresBroker

        dramatiq.set_encoder(JSONPickleEncoder())
        broker = PostgresBroker()
        broker.add_middleware(Prometheus())
        broker.add_middleware(AgeLimit(max_age=timedelta(days=30).total_seconds() * 1000))
        broker.add_middleware(TimeLimit())
        broker.add_middleware(Callbacks())
        broker.add_middleware(Retries(max_retries=3))
        dramatiq.set_broker(broker)
        return super().ready()
