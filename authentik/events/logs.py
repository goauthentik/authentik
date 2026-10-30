from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from django.utils.timezone import now
from rest_framework.fields import CharField, ChoiceField, DateTimeField, DictField
from structlog.stdlib import NAME_TO_LEVEL, get_logger
from structlog.types import EventDict

from authentik.core.api.utils import PassiveSerializer
from authentik.events.utils import sanitize_dict
from authentik.lib.logging import CAPTURED_LOGS


@dataclass()
class LogEvent:

    event: str
    log_level: str
    logger: str
    timestamp: datetime = field(default_factory=now)
    attributes: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_event_dict(item: EventDict) -> LogEvent:
        event = item.pop("event")
        log_level = item.pop("level").lower()
        timestamp = datetime.fromisoformat(item.pop("timestamp")).replace(tzinfo=UTC)
        item.pop("pid", None)
        # Sometimes log entries have both `level` and `log_level` set, but `level` is always set
        item.pop("log_level", None)
        return LogEvent(
            event, log_level, item.pop("logger"), timestamp, attributes=sanitize_dict(item)
        )

    def log(self):
        get_logger(self.logger).log(NAME_TO_LEVEL[self.log_level], self.event, **self.attributes)


class LogEventSerializer(PassiveSerializer):
    """Single log message with all context logged."""

    timestamp = DateTimeField()
    log_level = ChoiceField(choices=tuple((x, x) for x in NAME_TO_LEVEL.keys()))
    logger = CharField()
    event = CharField()
    attributes = DictField()


@contextmanager
def capture_logs(log_default_output=True) -> Generator[list[LogEvent]]:
    """Capture log entries created in the current context (thread/task)"""
    logs = []
    entries: list[EventDict] = []
    token = CAPTURED_LOGS.set(entries)
    try:
        yield logs
        for raw_log in entries:
            logs.append(LogEvent.from_event_dict(raw_log))
    finally:
        CAPTURED_LOGS.reset(token)
