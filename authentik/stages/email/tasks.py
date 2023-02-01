"""email stage tasks"""
from email.utils import make_msgid
from smtplib import SMTPException
from typing import Any, Optional

from celery import group
from django.core.mail import EmailMultiAlternatives
from django.core.mail.utils import DNS_NAME
from django.utils.text import slugify
from structlog.stdlib import get_logger

from authentik.events.models import Event, EventAction
from authentik.events.monitored_tasks import MonitoredTask, TaskResult, TaskResultStatus
from authentik.root.celery import CELERY_APP
from authentik.stages.email.models import EmailStage

LOGGER = get_logger()


def send_mails(stage: EmailStage, *messages: list[EmailMultiAlternatives]):
    """Wrapper to convert EmailMessage to dict and send it from worker"""
    tasks = []
    for message in messages:
        tasks.append(send_mail.s(message.__dict__, stage.pk))
    lazy_group = group(*tasks)
    promise = lazy_group()
    return promise


def get_email_body(email: EmailMultiAlternatives) -> str:
    """Get the email's body. Will return HTML alt if set, otherwise plain text body"""
    for alt_content, alt_type in email.alternatives:
        if alt_type == "text/html":
            return alt_content
    return email.body


@CELERY_APP.task(
    bind=True,
    autoretry_for=(
        SMTPException,
        ConnectionError,
        OSError,
    ),
    retry_backoff=True,
    base=MonitoredTask,
)
def send_mail(self: MonitoredTask, message: dict[Any, Any], email_stage_pk: Optional[int] = None):
    """Send Email for Email Stage. Retries are scheduled automatically."""
    self.save_on_success = False
    message_id = make_msgid(domain=DNS_NAME)
    self.set_uid(slugify(message_id.replace(".", "_").replace("@", "_")))
    try:
        if not email_stage_pk:
            stage: EmailStage = EmailStage(use_global_settings=True)
        else:
            stages = EmailStage.objects.filter(pk=email_stage_pk)
            if not stages.exists():
                self.set_status(
                    TaskResult(
                        TaskResultStatus.WARNING,
                        messages=["Email stage does not exist anymore. Discarding message."],
                    )
                )
                return
            stage: EmailStage = stages.first()
        try:
            backend = stage.backend
        except ValueError as exc:
            LOGGER.warning("failed to get email backend", exc=exc)
            self.set_status(TaskResult(TaskResultStatus.ERROR).with_error(exc))
            return
        backend.open()
        # Since django's EmailMessage objects are not JSON serialisable,
        # we need to rebuild them from a dict
        message_object = EmailMultiAlternatives()
        for key, value in message.items():
            setattr(message_object, key, value)
        if not stage.use_global_settings:
            message_object.from_email = stage.from_address
        # Because we use the Message-ID as UID for the task, manually assign it
        message_object.extra_headers["Message-ID"] = message_id

        LOGGER.debug("Sending mail", to=message_object.to)
        backend.send_messages([message_object])
        Event.new(
            EventAction.EMAIL_SENT,
            message=f"Email to {', '.join(message_object.to)} sent",
            subject=message_object.subject,
            body=get_email_body(message_object),
            from_email=message_object.from_email,
            to_email=message_object.to,
        ).save()
        self.set_status(
            TaskResult(
                TaskResultStatus.SUCCESSFUL,
                messages=["Successfully sent Mail."],
            )
        )
    except (SMTPException, ConnectionError, OSError) as exc:
        LOGGER.debug("Error sending email, retrying...", exc=exc)
        self.set_status(TaskResult(TaskResultStatus.ERROR).with_error(exc))
        raise exc
