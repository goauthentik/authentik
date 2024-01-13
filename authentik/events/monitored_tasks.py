"""Monitored tasks"""
from datetime import timedelta
from timeit import default_timer
from typing import Any, Optional

from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from structlog.stdlib import get_logger
from tenant_schemas_celery.task import TenantTask

from authentik.events.models import Event, EventAction, SystemTask, TaskStatus
from authentik.events.utils import sanitize_item
from authentik.lib.utils.errors import exception_to_string

LOGGER = get_logger()


class MonitoredTask(TenantTask):
    """Task which can save its state to the cache"""

    # For tasks that should only be listed if they failed, set this to False
    save_on_success: bool

    _status: Optional[TaskStatus]
    _messages: list[str]

    _uid: Optional[str]
    _start: Optional[float] = None

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.save_on_success = True
        self._uid = None
        self._status = None
        self._messages = []
        self.result_timeout_hours = 6

    def set_uid(self, uid: str):
        """Set UID, so in the case of an unexpected error its saved correctly"""
        self._uid = uid

    def set_status(self, status: TaskStatus, *messages: str):
        """Set result for current run, will overwrite previous result."""
        self._status = status
        self._messages = messages

    def set_error(self, exception: Exception):
        """Set result to error and save exception"""
        self._status = TaskStatus.ERROR
        self._messages = [exception_to_string(exception)]

    def before_start(self, task_id, args, kwargs):
        self._start = default_timer()
        return super().before_start(task_id, args, kwargs)

    # pylint: disable=too-many-arguments
    def after_return(self, status, retval, task_id, args: list[Any], kwargs: dict[str, Any], einfo):
        super().after_return(status, retval, task_id, args, kwargs, einfo=einfo)
        if not self._status:
            return
        if self._status == TaskStatus.SUCCESSFUL and not self.save_on_success:
            SystemTask.objects.filter(
                name=self.__name__,
                uid=self._uid,
            ).delete()
            return
        SystemTask.objects.update_or_create(
            name=self.__name__,
            uid=self._uid,
            defaults={
                "description": self.__doc__,
                "start_timestamp": self._start or default_timer(),
                "finish_timestamp": default_timer(),
                "task_call_module": self.__module__,
                "task_call_func": self.__name__,
                "task_call_args": args,
                "task_call_kwargs": kwargs,
                "status": self._status,
                "messages": sanitize_item(self._messages),
                "expires": now() + timedelta(hours=self.result_timeout_hours),
                "expiring": True,
            },
        )

    # pylint: disable=too-many-arguments
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        super().on_failure(exc, task_id, args, kwargs, einfo=einfo)
        if not self._status:
            self._status = TaskStatus.ERROR
            self._messages = exception_to_string(exc)
        SystemTask.objects.update_or_create(
            name=self.__name__,
            uid=self._uid,
            defaults={
                "description": self.__doc__,
                "start_timestamp": self._start or default_timer(),
                "finish_timestamp": default_timer(),
                "task_call_module": self.__module__,
                "task_call_func": self.__name__,
                "task_call_args": args,
                "task_call_kwargs": kwargs,
                "status": self._status,
                "messages": sanitize_item(self._messages),
                "expires": now() + timedelta(hours=self.result_timeout_hours),
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
        SystemTask(
            name=func.__name__,
            description=func.__doc__,
            status=TaskStatus.UNKNOWN,
            messages=sanitize_item([_("Task has not been run yet.")]),
            task_call_module=func.__module__,
            task_call_func=func.__name__,
            expiring=False,
        )
    )
    return func


_prefill_tasks = []
