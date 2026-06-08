import logging
from typing import Any, cast

import tenacity
from django.db import IntegrityError, transaction
from django.db.models import QuerySet
from django_dramatiq_postgres.broker import PostgresBroker as BasePostgresBroker
from django_dramatiq_postgres.broker import raise_broker_connection_error
from django_dramatiq_postgres.models import TaskState
from dramatiq.common import current_millis, q_name
from dramatiq.errors import BrokerConnectionError
from dramatiq.message import Message
from structlog.stdlib import get_logger

LOGGER = get_logger()


class Broker(BasePostgresBroker):
    @property
    def query_set(self) -> QuerySet:
        return super().query_set.select_related("tenant").filter(tenant__ready=True)

    def _active_task_for_uid(
        self,
        queue_name: str,
        actor_name: str,
        uid: str,
        tenant: Any,
    ):
        query = self.query_set.filter(
            queue_name=queue_name,
            actor_name=actor_name,
            _uid=uid,
            _deduplicate_by_uid=True,
        ).exclude(state__in=(TaskState.DONE, TaskState.REJECTED))
        if tenant is not None:
            query = query.filter(tenant=tenant)
        return query.defer(None).defer("result").order_by("mtime").first()

    def _coalesced_message(self, task) -> Message[Any]:
        message = Message.decode(bytes(task.message))
        message.options["task"] = task
        message.options["task_created"] = False
        message.options["task_coalesced"] = True
        return message

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(BrokerConnectionError),
        reraise=True,
        wait=tenacity.wait_random_exponential(multiplier=1, max=5),
        stop=tenacity.stop_after_attempt(3),
        before_sleep=tenacity.before_sleep_log(
            cast(logging.Logger, LOGGER), logging.INFO, exc_info=True
        ),
    )
    @raise_broker_connection_error
    def enqueue(self, message: Message[Any], *, delay: int | None = None) -> Message[Any]:
        queue_name = q_name(message.queue_name)
        if delay:
            message_eta = current_millis() + delay
            message.options["eta"] = message_eta

        self.declare_queue(queue_name)
        self.logger.debug(
            "Enqueueing message on queue", message_id=message.message_id, queue=queue_name
        )

        message.options["model_defaults"] = self.model_defaults(message)
        message.options["model_create_defaults"] = {}
        self.emit_before("enqueue", message, delay)

        defaults = message.options.pop("model_defaults")
        create_defaults_base = message.options.pop("model_create_defaults")
        uid = defaults.get("_uid")
        deduplicate_by_uid = defaults.get("_deduplicate_by_uid", False)
        tenant = create_defaults_base.get("tenant")

        for attempt in range(2):
            try:
                with transaction.atomic(using=self.db_alias):
                    if deduplicate_by_uid and uid:
                        task = self._active_task_for_uid(
                            queue_name=queue_name,
                            actor_name=message.actor_name,
                            uid=uid,
                            tenant=tenant,
                        )
                        if task:
                            coalesced_message = self._coalesced_message(task)
                            self.emit_after("enqueue", coalesced_message, delay)
                            return coalesced_message

                    query = {
                        "message_id": message.message_id,
                    }
                    create_defaults = {
                        **query,
                        **defaults,
                        **create_defaults_base,
                    }
                    defaults["message"] = message.encode()
                    create_defaults["message"] = defaults["message"]

                    task, created = self.query_set.update_or_create(
                        **query,
                        defaults=defaults,
                        create_defaults=create_defaults,
                    )
                    message.options["task"] = task
                    message.options["task_created"] = created

                    self.emit_after("enqueue", message, delay)
                    return message
            except IntegrityError:
                if not deduplicate_by_uid or not uid or attempt > 0:
                    raise

        return message


PostgresBroker = Broker
