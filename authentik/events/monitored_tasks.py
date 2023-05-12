"""Monitored tasks"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from timeit import default_timer
from typing import Any, Optional

from celery import Task
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from structlog.stdlib import get_logger

from authentik.events.apps import GAUGE_TASKS
from authentik.events.models import Event, EventAction
from authentik.lib.utils.errors import exception_to_string

LOGGER = get_logger()
CACHE_KEY_PREFIX = "goauthentik.io/events/tasks/"


class TaskResultStatus(Enum):
    """Possible states of tasks"""

    SUCCESSFUL = 1
    WARNING = 2
    ERROR = 4
    UNKNOWN = 8


@dataclass
class TaskResult:
    """Result of a task run, this class is created by the task itself
    and used by self.set_status"""

    status: TaskResultStatus

    messages: list[str] = field(default_factory=list)

    # Optional UID used in cache for tasks that run in different instances
    uid: Optional[str] = field(default=None)

    def with_error(self, exc: Exception) -> "TaskResult":
        """Since errors might not always be pickle-able, set the traceback"""
        self.messages.append(exception_to_string(exc))
        return self


@dataclass
class TaskInfo:
    """Info about a task run"""

    task_name: str
    start_timestamp: float
    finish_timestamp: float
    finish_time: datetime

    result: TaskResult

    task_call_module: str
    task_call_func: str
    task_call_args: list[Any] = field(default_factory=list)
    task_call_kwargs: dict[str, Any] = field(default_factory=dict)

    task_description: Optional[str] = field(default=None)

    @staticmethod
    def all() -> dict[str, "TaskInfo"]:
        """Get all TaskInfo objects"""
        return cache.get_many(cache.keys(CACHE_KEY_PREFIX + "*"))

    @staticmethod
    def by_name(name: str) -> Optional["TaskInfo"]:
        """Get TaskInfo Object by name"""
        return cache.get(CACHE_KEY_PREFIX + name, None)

    def delete(self):
        """Delete task info from cache"""
        return cache.delete(CACHE_KEY_PREFIX + self.task_name)

    def update_metrics(self):
        """Update prometheus metrics"""
        start = default_timer()
        if hasattr(self, "start_timestamp"):
            start = self.start_timestamp
        try:
            duration = max(self.finish_timestamp - start, 0)
        except TypeError:
            duration = 0
        GAUGE_TASKS.labels(
            task_name=self.task_name.split(":")[0],
            task_uid=self.result.uid or "",
            status=self.result.status.value,
        ).set(duration)

    def save(self, timeout_hours=6):
        """Save task into cache"""
        key = CACHE_KEY_PREFIX + self.task_name
        if self.result.uid:
            key += f":{self.result.uid}"
            self.task_name += f":{self.result.uid}"
        self.update_metrics()
        cache.set(key, self, timeout=timeout_hours * 60 * 60)


class MonitoredTask(Task):
    """Task which can save its state to the cache"""

    # For tasks that should only be listed if they failed, set this to False
    save_on_success: bool

    _result: Optional[TaskResult]

    _uid: Optional[str]
    start: Optional[float] = None

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.save_on_success = True
        self._uid = None
        self._result = None
        self.result_timeout_hours = 6

    def set_uid(self, uid: str):
        """Set UID, so in the case of an unexpected error its saved correctly"""
        self._uid = uid

    def set_status(self, result: TaskResult):
        """Set result for current run, will overwrite previous result."""
        self._result = result

    def before_start(self, task_id, args, kwargs):
        self.start = default_timer()
        return super().before_start(task_id, args, kwargs)

    # pylint: disable=too-many-arguments
    def after_return(self, status, retval, task_id, args: list[Any], kwargs: dict[str, Any], einfo):
        super().after_return(status, retval, task_id, args, kwargs, einfo=einfo)
        if not self._result:
            return
        if not self._result.uid:
            self._result.uid = self._uid
        info = TaskInfo(
            task_name=self.__name__,
            task_description=self.__doc__,
            start_timestamp=self.start or default_timer(),
            finish_timestamp=default_timer(),
            finish_time=datetime.now(),
            result=self._result,
            task_call_module=self.__module__,
            task_call_func=self.__name__,
            task_call_args=args,
            task_call_kwargs=kwargs,
        )
        if self._result.status == TaskResultStatus.SUCCESSFUL and not self.save_on_success:
            info.delete()
            return
        info.save(self.result_timeout_hours)

    # pylint: disable=too-many-arguments
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        super().on_failure(exc, task_id, args, kwargs, einfo=einfo)
        if not self._result:
            self._result = TaskResult(status=TaskResultStatus.ERROR, messages=[str(exc)])
        if not self._result.uid:
            self._result.uid = self._uid
        TaskInfo(
            task_name=self.__name__,
            task_description=self.__doc__,
            start_timestamp=self.start or default_timer(),
            finish_timestamp=default_timer(),
            finish_time=datetime.now(),
            result=self._result,
            task_call_module=self.__module__,
            task_call_func=self.__name__,
            task_call_args=args,
            task_call_kwargs=kwargs,
        ).save(self.result_timeout_hours)
        Event.new(
            EventAction.SYSTEM_TASK_EXCEPTION,
            message=f"Task {self.__name__} encountered an error: {exception_to_string(exc)}",
        ).save()

    def run(self, *args, **kwargs):
        raise NotImplementedError


def prefill_task(func):
    """Ensure a task's details are always in cache, so it can always be triggered via API"""
    status = TaskInfo.by_name(func.__name__)
    if status:
        return func
    TaskInfo(
        task_name=func.__name__,
        task_description=func.__doc__,
        result=TaskResult(TaskResultStatus.UNKNOWN, messages=[_("Task has not been run yet.")]),
        task_call_module=func.__module__,
        task_call_func=func.__name__,
        # We don't have real values for these attributes but they cannot be null
        start_timestamp=default_timer(),
        finish_timestamp=default_timer(),
        finish_time=datetime.now(),
    ).save(86400)
    LOGGER.debug("prefilled task", task_name=func.__name__)
    return func
