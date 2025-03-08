import pydoc
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field

from django_q import tasks
from django_q.brokers import get_broker
from django_q.conf import Conf
from django_q.humanhash import uuid
from django_q.models import Task

from authentik.events.logs import LogEvent
from authentik.lib.utils.errors import exception_to_string
from authentik.tasks.models import TaskExtra, TaskStatus
from structlog.stdlib import get_logger

LOGGER = get_logger()


@dataclass
class TaskData:
    uid: str = ""
    soft_status: TaskStatus = TaskStatus.UNKNOWN
    messages: list[LogEvent] = field(default_factory=list)
    description: str = ""

    def set_uid(self, uid: str):
        self.uid = uid

    def set_status(self, status: TaskStatus, *messages: LogEvent):
        self.status = status
        self.messages = list(messages)
        for idx, msg in enumerate(self.messages):
            if not isinstance(msg, LogEvent):
                self.messages[idx] = LogEvent(msg, logger=self.uid, log_level="info")

    def set_error(self, exception: Exception, *messages: LogEvent):
        self.status = TaskStatus.ERROR
        self.messages = list(messages)
        self.messages.extend(
            [LogEvent(exception_to_string(exception), logger=self.uid, log_level="error")]
        )


def _hook(task: Task):
    result, data = task.result
    TaskExtra.objects.update_or_create(
        task=task,
        defaults=asdict(data),
    )
    # Avoid post_save signal being sent
    Task.objects.filter(pk=task.pk).update(result=result)


def task(
    bind=False,
    throws: Iterable[type[Exception]] | None = None,
    autoretry_for: Iterable[type[Exception]] | None = None,
    retry_backoff: bool = False,
    timeout: int | None = None,
):
    def wrapper(func):
        def inner(*args, **kwargs):
            if bind:
                data = TaskData()
                return func(data, *args, **kwargs), data
            return func(*args, **kwargs)

        inner.bind = bind
        return inner

    return wrapper


def async_task(func: str, *args, **kwargs):
    """
    Wrapper around django_q's async_task to support various extra use-cases.

    Do not use raw async_task arguments, put them in a "q_options" dict arg.
    """
    if not isinstance(func, str):
        raise RuntimeError("async_task should be called with the task path")
    f = pydoc.locate(func)
    if f is None:
        LOGGER.error(f"Could not find task at {func}")
        raise RuntimeError(f"Could not find task at {func}")
    q_options = kwargs.pop("q_options", {})
    if f.bind and "hook" not in q_options:
        q_options["hook"] = "authentik.tasks.tasks._hook"
    return tasks.async_task(func, *args, q_options=q_options, **kwargs)


def async_iter(func, args_iter, **kwargs):
    """
    Wrapper around django_q's async_iter to support various extra use-cases.

    Do not use raw async_iter arguments, put them in a "q_options" dict arg.
    """
    if not isinstance(func, str):
        raise RuntimeError("async_iter should be called with the task path")
    f = pydoc.locate(func)
    q_options = kwargs.pop("q_options", {})
    if f.bind and "hook" not in q_options:
        q_options["hook"] = "authentik.tasks.tasks._hook"
    return tasks.async_iter(func, args_iter, q_options=q_options, **kwargs)


def async_chain(chain, group=None, cached=Conf.CACHED, sync=Conf.SYNC, broker=None):
    """
    Wrapper around django_q's async_chain to support various extra use-cases.

    Do not use raw async_task arguments, put them in a "q_options" dict arg.
    """
    if not group:
        group = uuid()[1]
    args = ()
    kwargs = {}
    task = chain.pop(0)
    if type(task) is not tuple:
        task = (task,)
    if len(task) > 1:
        args = task[1]
    if len(task) > 2:  # noqa: PLR2004
        kwargs = task[2]
    kwargs["chain"] = chain
    kwargs["group"] = group
    kwargs["cached"] = cached
    kwargs["sync"] = sync
    kwargs["broker"] = broker or get_broker()
    async_task(task[0], *args, **kwargs)
    return group


class Iter(tasks.Iter):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError


class Chain(tasks.Iter):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError


class AsyncTask(tasks.Iter):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError


result = tasks.result
result_cached = tasks.result_cached
result_group = tasks.result_group
result_group_cached = tasks.result_group_cached
fetch = tasks.fetch
fetch_cached = tasks.fetch_cached
fetch_group = tasks.fetch_group
fetch_group_cached = tasks.fetch_group_cached
count_group = tasks.count_group
count_group_cached = tasks.count_group_cached
delete_group = tasks.delete_group
delete_group_cached = tasks.delete_group_cached
delete_cached = tasks.delete_cached
queue_size = tasks.queue_size
