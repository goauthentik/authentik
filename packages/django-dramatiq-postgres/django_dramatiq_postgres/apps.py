import dramatiq
from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string
from dramatiq.results.middleware import Results

from django_dramatiq_postgres.conf import Conf


class DjangoDramatiqPostgres(AppConfig):
    name = "django_dramatiq_postgres"
    verbose_name = "Django Dramatiq postgres"

    def ready(self) -> None:
        try:
            old_broker = dramatiq.get_broker()
        except ModuleNotFoundError:
            old_broker = None

        if old_broker is not None and len(old_broker.actors) != 0:
            raise ImproperlyConfigured(
                "Actors were previously registered. "
                "Make sure your actors are not imported too early."
            )

        encoder: dramatiq.encoder.Encoder = import_string(Conf().encoder_class)()
        dramatiq.set_encoder(encoder)

        broker: dramatiq.broker.Broker = import_string(Conf().broker_class)(
            *Conf().broker_args,
            **Conf().broker_kwargs,
            middleware=[],
        )

        for middleware_class_path, middleware_kwargs in Conf().middlewares:
            middleware_class = import_string(middleware_class_path)
            if issubclass(middleware_class, Results):
                middleware_kwargs["backend"] = import_string(Conf().result_backend)(
                    *Conf().result_backend_args,
                    **Conf().result_backend_kwargs,
                )
            middleware: dramatiq.middleware.middleware.Middleware = middleware_class(
                **middleware_kwargs,
            )
            broker.add_middleware(middleware)

        dramatiq.set_broker(broker)

        return super().ready()
