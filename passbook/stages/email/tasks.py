"""email stage tasks"""
from smtplib import SMTPException
from typing import Any, Dict, List

from celery import group
from django.core.mail import EmailMultiAlternatives
from structlog import get_logger

from passbook.root.celery import CELERY_APP
from passbook.stages.email.models import EmailStage

LOGGER = get_logger()


def send_mails(stage: EmailStage, *messages: List[EmailMultiAlternatives]):
    """Wrapper to convert EmailMessage to dict and send it from worker"""
    tasks = []
    for message in messages:
        tasks.append(_send_mail_task.s(stage.pk, message.__dict__))
    lazy_group = group(*tasks)
    promise = lazy_group()
    return promise


@CELERY_APP.task(
    bind=True, autoretry_for=(SMTPException, ConnectionError,), retry_backoff=True
)
# pylint: disable=unused-argument
def _send_mail_task(self, email_stage_pk: int, message: Dict[Any, Any]):
    """Send Email according to EmailStage parameters from background worker.
    Automatically retries if message couldn't be sent."""
    stage: EmailStage = EmailStage.objects.get(pk=email_stage_pk)
    backend = stage.backend
    backend.open()
    # Since django's EmailMessage objects are not JSON serialisable,
    # we need to rebuild them from a dict
    message_object = EmailMultiAlternatives()
    for key, value in message.items():
        setattr(message_object, key, value)
    message_object.from_email = stage.from_address
    LOGGER.debug("Sending mail", to=message_object.to)
    stage.backend.send_messages([message_object])
