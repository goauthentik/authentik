from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from django.utils.timezone import now
from rest_framework.fields import CharField, ChoiceField, DateTimeField, DictField
from structlog import configure, get_config
from structlog.stdlib import NAME_TO_LEVEL, ProcessorFormatter
from structlog.testing import LogCapture
from structlog.types import EventDict

from authentik.core.api.utils import PassiveSerializer
from authentik.events.utils import sanitize_dict


@dataclass()
class LogEvent:

    event: str
    log_level: str
    logger: str
    timestamp: datetime = field(default_factory=now)
    attributes: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_event_dict(item: EventDict) -> "LogEvent":
        event = item.pop("event")
        log_level = item.pop("level").lower()
        timestamp = datetime.fromisoformat(item.pop("timestamp"))
        item.pop("pid", None)
        # Sometimes log entries have both `level` and `log_level` set, but `level` is always set
        item.pop("log_level", None)
        return LogEvent(
            event, log_level, item.pop("logger"), timestamp, attributes=sanitize_dict(item)
        )


class LogEventSerializer(PassiveSerializer):
    """Single log message with all context logged."""

    timestamp = DateTimeField()
    log_level = ChoiceField(choices=tuple((x, x) for x in NAME_TO_LEVEL.keys()))
    logger = CharField()
    event = CharField()
    attributes = DictField()

    # TODO(2024.6?): This is a migration helper to return a correct API response for logs that
    # have been saved in an older format (mostly just list[str] with just the messages)
    def to_representation(self, instance):
        if isinstance(instance, str):
            instance = LogEvent(instance, "", "")
        elif isinstance(instance, list):
            instance = [LogEvent(x, "", "") for x in instance]
        return super().to_representation(instance)


@contextmanager
def capture_logs(log_default_output=True) -> Generator[list[LogEvent]]:
    """Capture log entries created"""
    logs = []
    cap = LogCapture()
    # Modify `_Configuration.default_processors` set via `configure` but always
    # keep the list instance intact to not break references held by bound
    # loggers.
    processors: list = get_config()["processors"]
    old_processors = processors.copy()
    try:
        # clear processors list and use LogCapture for testing
        if ProcessorFormatter.wrap_for_formatter in processors:
            processors.remove(ProcessorFormatter.wrap_for_formatter)
        processors.append(cap)
        configure(processors=processors)
        yield logs
        for raw_log in cap.entries:
            logs.append(LogEvent.from_event_dict(raw_log))
    finally:
        # remove LogCapture and restore original processors
        processors.clear()
        processors.extend(old_processors)
        configure(processors=processors)
