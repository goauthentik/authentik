"""passbook core celery"""

import logging
import os

from celery import Celery, signals
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "passbook.root.settings")

LOGGER = logging.getLogger(__name__)


CELERY_APP = Celery('passbook')


# pylint: disable=unused-argument
@signals.setup_logging.connect
def config_loggers(*args, **kwags):
    """Apply logging settings from settings.py to celery"""
    logging.config.dictConfig(settings.LOGGING)


# pylint: disable=unused-argument
@signals.after_task_publish.connect
def after_task_publish(sender=None, headers=None, body=None, **kwargs):
    """Log task_id after it was published"""
    info = headers if 'task' in headers else body
    LOGGER.debug('%-40s published (name=%s)', info.get('id'), info.get('task'))


# pylint: disable=unused-argument
@signals.task_prerun.connect
def task_prerun(task_id, task, *args, **kwargs):
    """Log task_id on worker"""
    LOGGER.debug('%-40s started (name=%s)', task_id, task.__name__)


# pylint: disable=unused-argument
@signals.task_postrun.connect
def task_postrun(task_id, task, *args, retval=None, state=None, **kwargs):
    """Log task_id on worker"""
    LOGGER.debug('%-40s finished (name=%s, state=%s)',
                 task_id, task.__name__, state)


# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
CELERY_APP.config_from_object(settings, namespace='CELERY')

# Load task modules from all registered Django app configs.
CELERY_APP.autodiscover_tasks()
