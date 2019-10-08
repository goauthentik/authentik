"""email factor tasks"""
from smtplib import SMTPException
from typing import Any, Dict, List

from celery import group
from django.core.mail import EmailMessage

from passbook.factors.email.models import EmailFactor
from passbook.root.celery import CELERY_APP


def send_mails(factor: EmailFactor, *messages: List[EmailMessage]):
    """Wrapper to convert EmailMessage to dict and send it from worker"""
    tasks = []
    for message in messages:
        tasks.append(_send_mail_task.s(factor.pk, message.__dict__))
    lazy_group = group(*tasks)
    promise = lazy_group()
    return promise

@CELERY_APP.task(bind=True)
def _send_mail_task(self, email_factor_pk: int, message: Dict[Any, Any]):
    """Send E-Mail according to EmailFactor parameters from background worker.
    Automatically retries if message couldn't be sent."""
    factor: EmailFactor = EmailFactor.objects.get(pk=email_factor_pk)
    backend = factor.backend
    backend.open()
    # Since django's EmailMessage objects are not JSON serialisable,
    # we need to rebuild them from a dict
    message_object = EmailMessage()
    for key, value in message.items():
        setattr(message_object, key, value)
    message_object.from_email = factor.from_address
    try:
        num_sent = factor.backend.send_messages([message_object])
    except SMTPException as exc:
        raise self.retry(exc=exc)
    if num_sent != 1:
        raise self.retry()
