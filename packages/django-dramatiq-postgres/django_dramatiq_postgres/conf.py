from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class Conf:
    def __init__(self):
        try:
            _ = settings.DRAMATIQ
        except AttributeError as exc:
            raise ImproperlyConfigured("Setting DRAMATIQ not set.") from exc
        if "task_model" not in self.conf:
            raise ImproperlyConfigured("DRAMATIQ.task_model not defined")

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
    def task_model(self) -> str:
        return self.conf["task_model"]

    @property
    def task_purge_interval(self) -> int:
        # 24 hours
        return self.conf.get("task_purge_interval", 24 * 60 * 60)

    @property
    def task_expiration(self) -> int:
        # 30 days
        return self.conf.get("task_expiration", 60 * 60 * 24 * 30)

    @property
    def result_backend(self) -> str:
        return self.conf.get("result_backend", "django_dramatiq_postgres.results.PostgresBackend")

    @property
    def result_backend_args(self) -> tuple[Any]:
        return self.conf.get("result_backend_args", ())

    @property
    def result_backend_kwargs(self) -> dict[str, Any]:
        return self.conf.get("result_backend_kwargs", {})

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
            "watch_folder": ".",
            "watch_use_polling": False,
            "processes": None,
            "threads": None,
            "consumer_listen_timeout": 30,
            **self.conf.get("worker", {}),
        }

    @property
    def scheduler_class(self) -> str:
        return self.conf.get("scheduler_class", "django_dramatiq_postgres.scheduler.Scheduler")

    @property
    def schedule_model(self) -> str | None:
        return self.conf.get("schedule_model")

    @property
    def scheduler_interval(self) -> int:
        return self.conf.get("scheduler_interval", 60)

    @property
    def test(self) -> bool:
        return self.conf.get("test", False)
