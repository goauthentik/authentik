"""authentik core celery"""
import os
from logging.config import dictConfig

from celery import Celery
from celery.signals import after_task_publish, setup_logging, task_postrun, task_prerun
from django.conf import settings
from structlog.stdlib import get_logger

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authentik.root.settings")

LOGGER = get_logger()
CELERY_APP = Celery("authentik")


# pylint: disable=unused-argument
@setup_logging.connect
def config_loggers(*args, **kwags):
    """Apply logging settings from settings.py to celery"""
    dictConfig(settings.LOGGING)


# pylint: disable=unused-argument
@after_task_publish.connect
def after_task_publish(sender=None, headers=None, body=None, **kwargs):
    """Log task_id after it was published"""
    info = headers if "task" in headers else body
    LOGGER.debug(
        "Task published", task_id=info.get("id", ""), task_name=info.get("task", "")
    )


# pylint: disable=unused-argument
@task_prerun.connect
def task_prerun(task_id, task, *args, **kwargs):
    """Log task_id on worker"""
    LOGGER.debug("Task started", task_id=task_id, task_name=task.__name__)


# pylint: disable=unused-argument
@task_postrun.connect
def task_postrun(task_id, task, *args, retval=None, state=None, **kwargs):
    """Log task_id on worker"""
    LOGGER.debug("Task finished", task_id=task_id, task_name=task.__name__, state=state)


# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
CELERY_APP.config_from_object(settings, namespace="CELERY")

# Load task modules from all registered Django app configs.
CELERY_APP.autodiscover_tasks()
