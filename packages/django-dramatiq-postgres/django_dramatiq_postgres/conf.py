from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class Conf:
    def __init__(self):
        try:
            self.conf = settings.DRAMATIQ
        except AttributeError as exc:
            raise ImproperlyConfigured("Setting DRAMATIQ not set.") from exc
        if "task_class" not in self.conf:
            raise ImproperlyConfigured("DRAMATIQ.task_class not defined")

    @property
    def encoder_class(self) -> str:
        return self.conf.get("encoder_class", "dramatiq.encoder.PickleEncoder")

    @property
    def broker_class(self) -> str:
        return self.conf.get("broker_class", "django_dramatiq_postgres.broker.PostgresBroker")

    @property
    def broker_args(self) -> tuple[Any]:
        return self.conf.get("broker_args", ())

    @property
    def broker_kwargs(self) -> dict[str, Any]:
        return self.conf.get("broker_kwargs", {})

    @property
    def middlewares(self) -> tuple[tuple[str, dict[str, Any]]]:
        return self.conf.get(
            "middlewares",
            (
                ("django_dramatiq_postgres.middleware.DbConnectionMiddleware", {}),
                ("dramatiq.middleware.age_limit.AgeLimit", {}),
                ("dramatiq.middleware.time_limit.TimeLimit", {}),
                ("dramatiq.middleware.shutdown.ShutdownNotifications", {}),
                ("dramatiq.middleware.callbacks.Callbacks", {}),
                ("dramatiq.middleware.pipelines.Pipelines", {}),
                ("dramatiq.middleware.retries.Retries", {}),
            ),
        )

    @property
    def channel_prefix(self) -> str:
        return self.conf.get("channel_prefix", "dramatiq.tasks")

    @property
    def task_class(self) -> str:
        return self.conf["task_class"]

    @property
    def test(self) -> bool:
        return self.conf.get("test", False)
