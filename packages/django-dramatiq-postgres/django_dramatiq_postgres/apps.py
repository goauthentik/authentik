import dramatiq
from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from django_dramatiq_postgres.conf import Conf


class DjangoDramatiqPostgres(AppConfig):
    name = "django_dramatiq_postgres"
    verbose_name = "Django Dramatiq postgres"

    def ready(self):
        old_broker = dramatiq.get_broker()

        if len(old_broker.actors) != 0:
            raise ImproperlyConfigured(
                "Actors were previously registered. "
                "Make sure your actors are not imported too early."
            )

        encoder: dramatiq.encoder.Encoder = import_string(Conf.encoder_class)()
        dramatiq.set_encoder(encoder)

        broker_args = Conf.broker_args
        broker_kwargs = {
            **Conf.broker_kwargs,
            "middleware": [],
        }
        broker: dramatiq.broker.Broker = import_string(Conf.broker_class)(
            *broker_args,
            **broker_kwargs,
        )

        for middleware_class, middleware_kwargs in Conf.middlewares:
            middleware: dramatiq.middleware.middleware.Middleware = import_string(middleware_class)(
                **middleware_kwargs,
            )
            broker.add_middleware(middleware)

        dramatiq.set_broker(broker)

        return super().ready()
