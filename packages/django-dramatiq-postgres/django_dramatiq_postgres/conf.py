from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class Conf:
    def __init__(self):
        try:
            _ = settings.DRAMATIQ
        except AttributeError as exc:
            raise ImproperlyConfigured("Setting DRAMATIQ not set.") from exc
        if "task_class" not in self.conf:
            raise ImproperlyConfigured("DRAMATIQ.task_class not defined")

    @property
    def conf(self) -> dict[str, Any]:
        return settings.DRAMATIQ

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
        return self.conf.get("channel_prefix", "dramatiq")

    @property
    def task_class(self) -> str:
        return self.conf["task_class"]

    @property
    def autodiscovery(self) -> dict[str, Any]:
        autodiscovery = {
            "enabled": False,
            "setup_module": "django_dramatiq_postgres.setup",
            "apps_prefix": None,
            "actors_module_name": "tasks",
            "modules_callback": None,
            **self.conf.get("autodiscovery", {}),
        }
        if not autodiscovery["enabled"] and not autodiscovery["modules_callback"]:
            raise ImproperlyConfigured(
                "One of DRAMATIQ.autodiscovery.enabled or "
                "DRAMATIQ.autodiscovery.modules_callback must be configured."
            )
        return autodiscovery

    @property
    def worker(self) -> dict[str, Any]:
        return {
            "use_gevent": False,
            "watch": settings.DEBUG,
            "watch_use_polling": False,
            "processes": None,
            "threads": None,
            **self.conf.get("worker", {}),
        }

    @property
    def test(self) -> bool:
        return self.conf.get("test", False)
