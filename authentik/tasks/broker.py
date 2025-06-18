from typing import Any

from django_dramatiq_postgres.middleware import DbConnectionMiddleware
from django.db import (
    DEFAULT_DB_ALIAS,
)
from dramatiq.broker import Broker
from dramatiq.message import Message
from dramatiq.middleware import (
    AgeLimit,
    Callbacks,
    Middleware,
    Pipelines,
    Prometheus,
    Retries,
    ShutdownNotifications,
    TimeLimit,
)
from structlog.stdlib import get_logger
from django_dramatiq_postgres.broker import PostgresBroker as PostgresBrokerBase

from authentik.tasks.models import Task
from authentik.tenants.models import Tenant
from authentik.tenants.utils import get_current_tenant

LOGGER = get_logger()


class TenantMiddleware(Middleware):
    def before_process_message(self, broker: Broker, message: Message):
        Task.objects.select_related("tenant").get(message_id=message.message_id).tenant.activate()

    def after_process_message(self, *args, **kwargs):
        Tenant.deactivate()


class PostgresBroker(PostgresBrokerBase):
    def __init__(
        self,
        *args,
        middleware: list[Middleware] | None = None,
        db_alias: str = DEFAULT_DB_ALIAS,
        **kwargs,
    ):
        super().__init__(*args, middleware=[], **kwargs)
        self.logger = get_logger().bind()

        self.queues = set()
        self.actor_options = {
            "rel_obj",
        }

        self.db_alias = db_alias
        self.middleware = []
        self.add_middleware(DbConnectionMiddleware())
        self.add_middleware(TenantMiddleware())
        if middleware is None:
            for m in (
                Prometheus,
                AgeLimit,
                TimeLimit,
                ShutdownNotifications,
                Callbacks,
                Pipelines,
                Retries,
            ):
                self.add_middleware(m())
        for m in middleware or []:
            self.add_middleware(m)

    def model_defaults(self, message: Message) -> dict[str, Any]:
        rel_obj = message.options.get("rel_obj")
        if rel_obj:
            del message.options["rel_obj"]
        return {
            "tenant": get_current_tenant(),
            "rel_obj": rel_obj,
            **super().model_defaults(message),
        }
