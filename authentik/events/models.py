"""authentik events models"""

from inspect import getmodule, stack
from typing import Optional, Union
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.http import HttpRequest
from django.utils.translation import gettext as _
from requests import post
from structlog.stdlib import get_logger

from authentik import __version__
from authentik.core.middleware import (
    SESSION_IMPERSONATE_ORIGINAL_USER,
    SESSION_IMPERSONATE_USER,
)
from authentik.core.models import Group, User
from authentik.events.utils import cleanse_dict, get_user, sanitize_dict
from authentik.lib.utils.http import get_client_ip
from authentik.policies.models import PolicyBindingModel
from authentik.stages.email.tasks import send_mail
from authentik.stages.email.utils import TemplateEmailMessage

LOGGER = get_logger("authentik.events")


class EventAction(models.TextChoices):
    """All possible actions to save into the events log"""

    LOGIN = "login"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"

    USER_WRITE = "user_write"
    SUSPICIOUS_REQUEST = "suspicious_request"
    PASSWORD_SET = "password_set"  # noqa # nosec

    TOKEN_VIEW = "token_view"  # nosec

    INVITE_USED = "invitation_used"

    AUTHORIZE_APPLICATION = "authorize_application"
    SOURCE_LINKED = "source_linked"

    IMPERSONATION_STARTED = "impersonation_started"
    IMPERSONATION_ENDED = "impersonation_ended"

    POLICY_EXECUTION = "policy_execution"
    POLICY_EXCEPTION = "policy_exception"
    PROPERTY_MAPPING_EXCEPTION = "property_mapping_exception"

    CONFIGURATION_ERROR = "configuration_error"

    MODEL_CREATED = "model_created"
    MODEL_UPDATED = "model_updated"
    MODEL_DELETED = "model_deleted"

    UPDATE_AVAILABLE = "update_available"

    CUSTOM_PREFIX = "custom_"


class Event(models.Model):
    """An individual Audit/Metrics/Notification/Error Event"""

    event_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    user = models.JSONField(default=dict)
    action = models.TextField(choices=EventAction.choices)
    app = models.TextField()
    context = models.JSONField(default=dict, blank=True)
    client_ip = models.GenericIPAddressField(null=True)
    created = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def _get_app_from_request(request: HttpRequest) -> str:
        if not isinstance(request, HttpRequest):
            return ""
        return request.resolver_match.app_name

    @staticmethod
    def new(
        action: Union[str, EventAction],
        app: Optional[str] = None,
        _inspect_offset: int = 1,
        **kwargs,
    ) -> "Event":
        """Create new Event instance from arguments. Instance is NOT saved."""
        if not isinstance(action, EventAction):
            action = EventAction.CUSTOM_PREFIX + action
        if not app:
            app = getmodule(stack()[_inspect_offset][0]).__name__
        cleaned_kwargs = cleanse_dict(sanitize_dict(kwargs))
        event = Event(action=action, app=app, context=cleaned_kwargs)
        return event

    def set_user(self, user: User) -> "Event":
        """Set `.user` based on user, ensuring the correct attributes are copied.
        This should only be used when self.from_http is *not* used."""
        self.user = get_user(user)
        return self

    def from_http(
        self, request: HttpRequest, user: Optional[settings.AUTH_USER_MODEL] = None
    ) -> "Event":
        """Add data from a Django-HttpRequest, allowing the creation of
        Events independently from requests.
        `user` arguments optionally overrides user from requests."""
        if hasattr(request, "user"):
            original_user = None
            if hasattr(request, "session"):
                original_user = request.session.get(
                    SESSION_IMPERSONATE_ORIGINAL_USER, None
                )
            self.user = get_user(request.user, original_user)
        if user:
            self.user = get_user(user)
        # Check if we're currently impersonating, and add that user
        if hasattr(request, "session"):
            if SESSION_IMPERSONATE_ORIGINAL_USER in request.session:
                self.user = get_user(request.session[SESSION_IMPERSONATE_ORIGINAL_USER])
                self.user["on_behalf_of"] = get_user(
                    request.session[SESSION_IMPERSONATE_USER]
                )
        # User 255.255.255.255 as fallback if IP cannot be determined
        self.client_ip = get_client_ip(request) or "255.255.255.255"
        # If there's no app set, we get it from the requests too
        if not self.app:
            self.app = Event._get_app_from_request(request)
        self.save()
        return self

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(
                "you may not edit an existing %s" % self._meta.model_name
            )
        LOGGER.debug(
            "Created Event",
            action=self.action,
            context=self.context,
            client_ip=self.client_ip,
            user=self.user,
        )
        return super().save(*args, **kwargs)

    @property
    def summary(self) -> str:
        """Return a summary of this event."""
        if "message" in self.context:
            return self.context["message"]
        return f"{self.action}: {self.context}"

    def __str__(self) -> str:
        return f"<Event action={self.action} user={self.user} context={self.context}>"

    class Meta:

        verbose_name = _("Event")
        verbose_name_plural = _("Events")


class TransportMode(models.TextChoices):
    """Modes that a notification transport can send a notification"""

    WEBHOOK = "webhook", _("Generic Webhook")
    WEBHOOK_SLACK = "webhook_slack", _("Slack Webhook (Slack/Discord)")
    EMAIL = "email", _("Email")


class NotificationTransport(models.Model):
    """Action which is executed when a Trigger matches"""

    uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    name = models.TextField(unique=True)
    mode = models.TextField(choices=TransportMode.choices)

    webhook_url = models.TextField(blank=True)

    def send(self, notification: "Notification") -> list[str]:
        """Send notification to user, called from async task"""
        if self.mode == TransportMode.WEBHOOK:
            return self.send_webhook(notification)
        if self.mode == TransportMode.WEBHOOK_SLACK:
            return self.send_webhook_slack(notification)
        if self.mode == TransportMode.EMAIL:
            return self.send_email(notification)
        raise ValueError(f"Invalid mode {self.mode} set")

    def send_webhook(self, notification: "Notification") -> list[str]:
        """Send notification to generic webhook"""
        response = post(
            self.webhook_url,
            json={
                "body": notification.body,
                "severity": notification.severity,
            },
        )
        return [
            response.status_code,
            response.text,
        ]

    def send_webhook_slack(self, notification: "Notification") -> list[str]:
        """Send notification to slack or slack-compatible endpoints"""
        body = {
            "username": "authentik",
            "icon_url": "https://goauthentik.io/img/icon.png",
            "attachments": [
                {
                    "author_name": "authentik",
                    "author_link": "https://goauthentik.io",
                    "author_icon": "https://goauthentik.io/img/icon.png",
                    "title": notification.body,
                    "color": "#fd4b2d",
                    "fields": [
                        {
                            "title": _("Severity"),
                            "value": notification.severity,
                            "short": True,
                        },
                        {
                            "title": _("Dispatched for user"),
                            "value": str(notification.user),
                            "short": True,
                        },
                    ],
                    "footer": f"authentik v{__version__}",
                }
            ],
        }
        if notification.event:
            body["attachments"][0]["title"] = notification.event.action
            body["attachments"][0]["text"] = notification.event.action
        response = post(self.webhook_url, json=body)
        return [
            response.status_code,
            response.text,
        ]

    def send_email(self, notification: "Notification") -> list[str]:
        """Send notification via global email configuration"""
        body_trunc = (
            (notification.body[:75] + "..")
            if len(notification.body) > 75
            else notification.body
        )
        mail = TemplateEmailMessage(
            subject=f"authentik Notification: {body_trunc}",
            template_name="email/setup.html",
            to=[notification.user.email],
            template_context={
                "body": notification.body,
            },
        )
        # Email is sent directly here, as the call to send() should have been from a task.
        # pyright: reportGeneralTypeIssues=false
        return send_mail(mail.__dict__)  # pylint: disable=no-value-for-parameter

    class Meta:

        verbose_name = _("Notification Transport")
        verbose_name_plural = _("Notification Transports")


class NotificationSeverity(models.TextChoices):
    """Severity images that a notification can have"""

    NOTICE = "notice", _("Notice")
    WARNING = "warning", _("Warning")
    ALERT = "alert", _("Alert")


class Notification(models.Model):
    """Event Notification"""

    uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    severity = models.TextField(choices=NotificationSeverity.choices)
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True)
    seen = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self) -> str:
        body_trunc = (self.body[:75] + "..") if len(self.body) > 75 else self.body
        return f"Notification for user {self.user}: {body_trunc}"

    class Meta:

        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")


class NotificationTrigger(PolicyBindingModel):
    """Decide when to create a Notification based on policies attached to this object."""

    name = models.TextField(unique=True)
    transports = models.ManyToManyField(
        NotificationTransport,
        help_text=_(
            (
                "Select which transports should be used to notify the user. If none are "
                "selected, the notification will only be shown in the authentik UI."
            )
        ),
    )
    severity = models.TextField(
        choices=NotificationSeverity.choices,
        default=NotificationSeverity.NOTICE,
        help_text=_(
            "Controls which severity level the created notifications will have."
        ),
    )
    group = models.ForeignKey(
        Group,
        help_text=_(
            (
                "Define which group of users this notification should be sent and shown to. "
                "If left empty, Notification won't ben sent."
            )
        ),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    class Meta:

        verbose_name = _("Notification Trigger")
        verbose_name_plural = _("Notification Triggers")
