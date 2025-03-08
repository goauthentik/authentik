"""authentik core celery"""

import os
from collections.abc import Callable
from contextvars import ContextVar
from logging.config import dictConfig
from pathlib import Path
from tempfile import gettempdir

from celery import bootsteps
from celery.apps.worker import Worker
from celery.signals import (
    after_task_publish,
    setup_logging,
    task_failure,
    task_internal_error,
    task_postrun,
    task_prerun,
    worker_ready,
)
from celery.worker.control import inspect_command
from django.conf import settings
from django.db import ProgrammingError
from django_tenants.utils import get_public_schema_name
from structlog.contextvars import STRUCTLOG_KEY_PREFIX
from structlog.stdlib import get_logger
from tenant_schemas_celery.app import CeleryApp as TenantAwareCeleryApp

from authentik import get_full_version
from authentik.lib.sentry import before_send
from authentik.lib.utils.errors import exception_to_string

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authentik.root.settings")

LOGGER = get_logger()
CELERY_APP = TenantAwareCeleryApp("authentik")
CTX_TASK_ID = ContextVar(STRUCTLOG_KEY_PREFIX + "task_id", default=Ellipsis)
HEARTBEAT_FILE = Path(gettempdir() + "/authentik-worker")


@after_task_publish.connect
def after_task_publish_hook(sender=None, headers=None, body=None, **kwargs):
    """Log task_id after it was published"""
    info = headers if "task" in headers else body
    LOGGER.info(
        "Task published",
        task_id=info.get("id", "").replace("-", ""),
        task_name=info.get("task", ""),
    )


@task_prerun.connect
def task_prerun_hook(task_id: str, task, *args, **kwargs):
    """Log task_id on worker"""
    request_id = "task-" + task_id.replace("-", "")
    CTX_TASK_ID.set(request_id)
    LOGGER.info("Task started", task_id=task_id, task_name=task.__name__)


@task_postrun.connect
def task_postrun_hook(task_id: str, task, *args, retval=None, state=None, **kwargs):
    """Log task_id on worker"""
    CTX_TASK_ID.set(...)
    LOGGER.info(
        "Task finished", task_id=task_id.replace("-", ""), task_name=task.__name__, state=state
    )


@task_failure.connect
@task_internal_error.connect
def task_error_hook(task_id: str, exception: Exception, traceback, *args, **kwargs):
    """Create system event for failed task"""
    from authentik.events.models import Event, EventAction

    LOGGER.warning("Task failure", task_id=task_id.replace("-", ""), exc=exception)
    CTX_TASK_ID.set(...)
    if before_send({}, {"exc_info": (None, exception, None)}) is not None:
        Event.new(
            EventAction.SYSTEM_EXCEPTION, message=exception_to_string(exception), task_id=task_id
        ).save()


@worker_ready.connect
def worker_ready_hook(*args, **kwargs):
    """Run certain tasks on worker start"""
    from authentik.blueprints.v1.tasks import start_blueprint_watcher

    start_blueprint_watcher()


class LivenessProbe(bootsteps.StartStopStep):
    """Add a timed task to touch a temporary file for healthchecking reasons"""

    requires = {"celery.worker.components:Timer"}

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.requests = []
        self.tref = None

    def start(self, parent: Worker):
        self.tref = parent.timer.call_repeatedly(
            10.0,
            self.update_heartbeat_file,
            (parent,),
            priority=10,
        )
        self.update_heartbeat_file(parent)

    def stop(self, parent: Worker):
        HEARTBEAT_FILE.unlink(missing_ok=True)

    def update_heartbeat_file(self, worker: Worker):
        """Touch heartbeat file"""
        HEARTBEAT_FILE.touch()


@inspect_command(default_timeout=0.2)
def ping(state, **kwargs):
    """Ping worker(s)."""
    return {"ok": "pong", "version": get_full_version()}


CELERY_APP.config_from_object(settings.CELERY)

# Load task modules from all registered Django app configs.
CELERY_APP.autodiscover_tasks()
CELERY_APP.steps["worker"].add(LivenessProbe)
