"""email stage tasks"""

from email.utils import make_msgid
from smtplib import SMTPException
from typing import Any

from celery import group
from django.core.mail import EmailMultiAlternatives
from django.core.mail.utils import DNS_NAME
from django.utils.text import slugify
from structlog.stdlib import get_logger

from authentik.events.models import Event, EventAction, TaskStatus
from authentik.events.system_tasks import SystemTask
from authentik.root.celery import CELERY_APP
from authentik.stages.authenticator_email.models import AuthenticatorEmailStage
from authentik.stages.email.models import EmailStage
from authentik.stages.email.utils import logo_data

LOGGER = get_logger()


def send_mails(
    stage: EmailStage | AuthenticatorEmailStage, *messages: list[EmailMultiAlternatives]
):
    """Wrapper to convert EmailMessage to dict and send it from worker

    Args:
        stage: Either an EmailStage or AuthenticatorEmailStage instance
        messages: List of email messages to send
    Returns:
        Celery group promise for the email sending tasks
    """
    tasks = []
    stage_class = stage.__class__
    for message in messages:
        tasks.append(send_mail.s(message.__dict__, stage_class, str(stage.pk)))
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
    base=SystemTask,
)
def send_mail(
    self: SystemTask,
    message: dict[Any, Any],
    stage_class: EmailStage | AuthenticatorEmailStage,
    email_stage_pk: str | None = None,
):
    """Send Email for Email Stage. Retries are scheduled automatically."""
    self.save_on_success = False
    message_id = make_msgid(domain=DNS_NAME)
    self.set_uid(slugify(message_id.replace(".", "_").replace("@", "_")))
    try:
        if not email_stage_pk:
            stage: EmailStage | AuthenticatorEmailStage = stage_class(use_global_settings=True)
        else:
            stages = stage_class.objects.filter(pk=email_stage_pk)
            if not stages.exists():
                self.set_status(
                    TaskStatus.WARNING,
                    "Email stage does not exist anymore. Discarding message.",
                )
                return
            stage: EmailStage | AuthenticatorEmailStage = stages.first()
        try:
            backend = stage.backend
        except ValueError as exc:
            LOGGER.warning("failed to get email backend", exc=exc)
            self.set_error(exc)
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

        # Add the logo (we can't add it in the previous message since MIMEImage
        # can't be converted to json)
        message_object.attach(logo_data())

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
            TaskStatus.SUCCESSFUL,
            "Successfully sent Mail.",
        )
    except (SMTPException, ConnectionError, OSError) as exc:
        LOGGER.debug("Error sending email, retrying...", exc=exc)
        self.set_error(exc)
        raise exc
