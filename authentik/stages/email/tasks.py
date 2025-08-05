"""email stage tasks"""

from email.utils import make_msgid
from typing import Any

from django.core.mail import EmailMultiAlternatives
from django.core.mail.utils import DNS_NAME
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_dramatiq_postgres.middleware import CurrentTask
from dramatiq.actor import actor
from dramatiq.composition import group
from structlog.stdlib import get_logger

from authentik.events.models import Event, EventAction
from authentik.lib.utils.reflection import class_to_path, path_to_class
from authentik.stages.authenticator_email.models import AuthenticatorEmailStage
from authentik.stages.email.models import EmailStage
from authentik.stages.email.utils import logo_data
from authentik.tasks.models import Task

LOGGER = get_logger()


def send_mails(
    stage: EmailStage | AuthenticatorEmailStage, *messages: list[EmailMultiAlternatives]
):
    """Wrapper to convert EmailMessage to dict and send it from worker

    Args:
        stage: Either an EmailStage or AuthenticatorEmailStage instance
        messages: List of email messages to send
    Returns:
        Dramatiq group promise for the email sending tasks
    """
    tasks = []
    # Use the class path instead of the class itself for serialization
    stage_class_path = class_to_path(stage.__class__)
    for message in messages:
        tasks.append(send_mail.message(message.__dict__, stage_class_path, str(stage.pk)))
    return group(tasks).run()


def get_email_body(email: EmailMultiAlternatives) -> str:
    """Get the email's body. Will return HTML alt if set, otherwise plain text body"""
    for alt_content, alt_type in email.alternatives:
        if alt_type == "text/html":
            return alt_content
    return email.body


@actor(description=_("Send email."))
def send_mail(
    message: dict[Any, Any],
    stage_class_path: str | None = None,
    email_stage_pk: str | None = None,
):
    """Send Email for Email Stage. Retries are scheduled automatically."""
    self: Task = CurrentTask.get_task()
    message_id = make_msgid(domain=DNS_NAME)
    self.set_uid(slugify(message_id.replace(".", "_").replace("@", "_")))
    if not stage_class_path or not email_stage_pk:
        stage = EmailStage(use_global_settings=True)
    else:
        stage_class = path_to_class(stage_class_path)
        stages = stage_class.objects.filter(pk=email_stage_pk)
        if not stages.exists():
            self.warning("Email stage does not exist anymore. Discarding message.")
            return
        stage: EmailStage | AuthenticatorEmailStage = stages.first()
    try:
        backend = stage.backend
    except ValueError as exc:
        LOGGER.warning("failed to get email backend", exc=exc)
        self.error(exc)
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

    # Add the logo if it is used in the email body (we can't add it in the
    # previous message since MIMEImage can't be converted to json)
    body = get_email_body(message_object)
    if "cid:logo" in body:
        message_object.attach(logo_data())

    if (
        message_object.to
        and isinstance(message_object.to[0], str)
        and "=?utf-8?" in message_object.to[0]
    ):
        message_object.to = [message_object.to[0].split("<")[-1].replace(">", "")]

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
    self.info("Successfully sent mail.")
