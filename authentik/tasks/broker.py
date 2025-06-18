from typing import Any

from django_dramatiq_postgres.broker import PostgresBroker
from dramatiq.message import Message
from structlog.stdlib import get_logger

from authentik.tenants.utils import get_current_tenant

LOGGER = get_logger()


class Broker(PostgresBroker):
    def model_defaults(self, message: Message) -> dict[str, Any]:
        rel_obj = message.options.get("rel_obj")
        if rel_obj:
            del message.options["rel_obj"]
        return {
            "tenant": get_current_tenant(),
            "rel_obj": rel_obj,
            **super().model_defaults(message),
        }
