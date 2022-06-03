"""authentik core celery"""
import os
from logging.config import dictConfig

from celery import Celery
from celery.signals import (
    after_task_publish,
    setup_logging,
    task_failure,
    task_internal_error,
    task_postrun,
    task_prerun,
    worker_ready,
)
from django.conf import settings
from django.db import ProgrammingError
from structlog.stdlib import get_logger

from authentik.core.middleware import LOCAL
from authentik.lib.sentry import before_send
from authentik.lib.utils.errors import exception_to_string

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authentik.root.settings")

LOGGER = get_logger()
CELERY_APP = Celery("authentik")


# pylint: disable=unused-argument
@setup_logging.connect
def config_loggers(*args, **kwargs):
    """Apply logging settings from settings.py to celery"""
    dictConfig(settings.LOGGING)


# pylint: disable=unused-argument
@after_task_publish.connect
def after_task_publish_hook(sender=None, headers=None, body=None, **kwargs):
    """Log task_id after it was published"""
    info = headers if "task" in headers else body
    LOGGER.info("Task published", task_id=info.get("id", ""), task_name=info.get("task", ""))


# pylint: disable=unused-argument
@task_prerun.connect
def task_prerun_hook(task_id: str, task, *args, **kwargs):
    """Log task_id on worker"""
    request_id = "task-" + task_id.replace("-", "")
    LOCAL.authentik_task = {
        "request_id": request_id,
    }
    LOGGER.info("Task started", task_id=task_id, task_name=task.__name__)


# pylint: disable=unused-argument
@task_postrun.connect
def task_postrun_hook(task_id, task, *args, retval=None, state=None, **kwargs):
    """Log task_id on worker"""
    LOGGER.info("Task finished", task_id=task_id, task_name=task.__name__, state=state)
    if not hasattr(LOCAL, "authentik_task"):
        return
    for key in list(LOCAL.authentik_task.keys()):
        del LOCAL.authentik_task[key]


# pylint: disable=unused-argument
@task_failure.connect
@task_internal_error.connect
def task_error_hook(task_id, exception: Exception, traceback, *args, **kwargs):
    """Create system event for failed task"""
    from authentik.events.models import Event, EventAction

    LOGGER.warning("Task failure", exc=exception)
    if before_send({}, {"exc_info": (None, exception, None)}) is not None:
        Event.new(EventAction.SYSTEM_EXCEPTION, message=exception_to_string(exception)).save()


@worker_ready.connect
def worker_ready_hook(*args, **kwargs):
    """Run certain tasks on worker start"""
    from authentik.admin.tasks import clear_update_notifications
    from authentik.managed.tasks import managed_reconcile
    from authentik.outposts.tasks import outpost_controller_all, outpost_local_connection
    from authentik.providers.proxy.tasks import proxy_set_defaults

    tasks = [
        clear_update_notifications,
        outpost_local_connection,
        outpost_controller_all,
        proxy_set_defaults,
        managed_reconcile,
    ]
    LOGGER.info("Dispatching startup tasks...")
    for task in tasks:
        try:
            task.delay()
        except ProgrammingError as exc:
            LOGGER.warning("Startup task failed", task=task, exc=exc)


# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
CELERY_APP.config_from_object(settings, namespace="CELERY")

# Load task modules from all registered Django app configs.
CELERY_APP.autodiscover_tasks()
