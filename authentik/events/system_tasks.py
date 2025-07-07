"""Monitored tasks"""

from datetime import datetime, timedelta
from time import perf_counter
from typing import Any

from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from structlog.stdlib import BoundLogger, get_logger
from tenant_schemas_celery.task import TenantTask

from authentik.events.logs import LogEvent
from authentik.events.models import Event, EventAction, TaskStatus
from authentik.events.models import SystemTask as DBSystemTask
from authentik.events.utils import sanitize_item
from authentik.lib.utils.errors import exception_to_string


class SystemTask(TenantTask):
    """Task which can save its state to the cache"""

    logger: BoundLogger

    # For tasks that should only be listed if they failed, set this to False
    save_on_success: bool

    _status: TaskStatus
    _messages: list[LogEvent]

    _uid: str | None
    # Precise start time from perf_counter
    _start_precise: float | None = None
    _start: datetime | None = None

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._status = TaskStatus.SUCCESSFUL
        self.save_on_success = True
        self._uid = None
        self._status = None
        self._messages = []
        self.result_timeout_hours = 6

    def set_uid(self, uid: str):
        """Set UID, so in the case of an unexpected error its saved correctly"""
        self._uid = uid

    def set_status(self, status: TaskStatus, *messages: LogEvent):
        """Set result for current run, will overwrite previous result."""
        self._status = status
        self._messages = list(messages)
        for idx, msg in enumerate(self._messages):
            if not isinstance(msg, LogEvent):
                self._messages[idx] = LogEvent(msg, logger=self.__name__, log_level="info")

    def set_error(self, exception: Exception, *messages: LogEvent):
        """Set result to error and save exception"""
        self._status = TaskStatus.ERROR
        self._messages = list(messages)
        self._messages.extend(
            [LogEvent(exception_to_string(exception), logger=self.__name__, log_level="error")]
        )

    def before_start(self, task_id, args, kwargs):
        self._start_precise = perf_counter()
        self._start = now()
        self.logger = get_logger().bind(task_id=task_id)
        return super().before_start(task_id, args, kwargs)

    def db(self) -> DBSystemTask | None:
        """Get DB object for latest task"""
        return DBSystemTask.objects.filter(
            name=self.__name__,
            uid=self._uid,
        ).first()

    def after_return(self, status, retval, task_id, args: list[Any], kwargs: dict[str, Any], einfo):
        super().after_return(status, retval, task_id, args, kwargs, einfo=einfo)
        if not self._status:
            return
        if self._status == TaskStatus.SUCCESSFUL and not self.save_on_success:
            DBSystemTask.objects.filter(
                name=self.__name__,
                uid=self._uid,
            ).delete()
            return
        DBSystemTask.objects.update_or_create(
            name=self.__name__,
            uid=self._uid,
            defaults={
                "description": self.__doc__,
                "start_timestamp": self._start or now(),
                "finish_timestamp": now(),
                "duration": max(perf_counter() - self._start_precise, 0),
                "task_call_module": self.__module__,
                "task_call_func": self.__name__,
                "task_call_args": sanitize_item(args),
                "task_call_kwargs": sanitize_item(kwargs),
                "status": self._status,
                "messages": sanitize_item(self._messages),
                "expires": now() + timedelta(hours=self.result_timeout_hours),
                "expiring": True,
            },
        )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        super().on_failure(exc, task_id, args, kwargs, einfo=einfo)
        if not self._status:
            self.set_error(exc)
        DBSystemTask.objects.update_or_create(
            name=self.__name__,
            uid=self._uid,
            defaults={
                "description": self.__doc__,
                "start_timestamp": self._start or now(),
                "finish_timestamp": now(),
                "duration": max(perf_counter() - self._start_precise, 0),
                "task_call_module": self.__module__,
                "task_call_func": self.__name__,
                "task_call_args": sanitize_item(args),
                "task_call_kwargs": sanitize_item(kwargs),
                "status": self._status,
                "messages": sanitize_item(self._messages),
                "expires": now() + timedelta(hours=self.result_timeout_hours + 3),
                "expiring": True,
            },
        )
        Event.new(
            EventAction.SYSTEM_TASK_EXCEPTION,
            message=f"Task {self.__name__} encountered an error: {exception_to_string(exc)}",
        ).save()

    def run(self, *args, **kwargs):
        raise NotImplementedError


def prefill_task(func):
    """Ensure a task's details are always in cache, so it can always be triggered via API"""
    _prefill_tasks.append(
        DBSystemTask(
            name=func.__name__,
            description=func.__doc__,
            start_timestamp=now(),
            finish_timestamp=now(),
            status=TaskStatus.UNKNOWN,
            messages=sanitize_item([_("Task has not been run yet.")]),
            task_call_module=func.__module__,
            task_call_func=func.__name__,
            expiring=False,
            duration=0,
        )
    )
    return func


_prefill_tasks = []
