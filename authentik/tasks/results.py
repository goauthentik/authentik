from django.db import DEFAULT_DB_ALIAS
from django.db.models import QuerySet
from django.utils import timezone
from dramatiq.message import Message, get_encoder
from dramatiq.results.backend import Missing, MResult, Result, ResultBackend

from authentik.tasks.models import Task, TaskState


class PostgresBackend(ResultBackend):
    def __init__(self, *args, db_alias: str = DEFAULT_DB_ALIAS, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_alias = db_alias

    @property
    def query_set(self) -> QuerySet:
        return Task.objects.using(self.db_alias)

    def build_message_key(self, message: Message) -> str:
        return str(message.message_id)

    def _get(self, message_key: str) -> MResult:
        message = self.query_set.filter(message_id=message_key).first()
        if message is None:
            return Missing
        data = message.result
        if data is None:
            return Missing
        return self.encoder.decode(data)

    def _store(self, message_key: str, result: Result, ttl: int) -> None:
        encoder = get_encoder()
        self.query_set.filter(message_id=message_key).update(
            mtime=timezone.now(),
            result=encoder.encode(result),
            result_ttl=timezone.now() + timezone.timedelta(milliseconds=ttl),
        )
