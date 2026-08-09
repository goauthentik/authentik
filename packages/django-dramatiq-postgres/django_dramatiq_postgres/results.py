from datetime import timedelta
from typing import Any, cast

from django.db import DEFAULT_DB_ALIAS
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from dramatiq.message import Message
from dramatiq.results.backend import Missing, MResult, Result, ResultBackend

from django_dramatiq_postgres.conf import Conf
from django_dramatiq_postgres.models import TaskBase


class PostgresBackend(ResultBackend):
    def __init__(self, *args: Any, db_alias: str = DEFAULT_DB_ALIAS, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.db_alias = db_alias

    @cached_property
    def model(self) -> type[TaskBase]:
        model: type[TaskBase] = import_string(Conf().task_model)
        return model

    @property
    def query_set(self) -> QuerySet[TaskBase]:
        return self.model._default_manager.using(self.db_alias).defer("message")

    def build_message_key(self, message: Message[Result]) -> str:
        return str(message.message_id)

    def _get(self, message_key: str) -> MResult:
        message = self.query_set.filter(message_id=message_key).first()
        if message is None:
            return Missing
        data = cast(bytes | None, message.result)
        if data is None:
            return Missing
        return self.encoder.decode(data)

    def _store(self, message_key: str, result: Result, ttl: int) -> None:
        self.query_set.filter(message_id=message_key).update(
            mtime=timezone.now(),
            result=self.encoder.encode(result),
            result_expiry=timezone.now() + timedelta(milliseconds=ttl),
        )
