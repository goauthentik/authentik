"""authentik events models"""

from collections.abc import Generator
from datetime import timedelta
from difflib import get_close_matches
from functools import lru_cache
from inspect import currentframe
from typing import Any
from uuid import uuid4

from django.apps import apps
from django.db import models
from django.http import HttpRequest
from django.http.request import QueryDict
from django.utils.timezone import now
from django.utils.translation import gettext as _
from requests import RequestException
from rest_framework.serializers import Serializer
from structlog.stdlib import get_logger

from authentik import get_full_version
from authentik.brands.models import Brand
from authentik.brands.utils import DEFAULT_BRAND
from authentik.core.middleware import (
    SESSION_KEY_IMPERSONATE_ORIGINAL_USER,
    SESSION_KEY_IMPERSONATE_USER,
)
from authentik.core.models import ExpiringModel, Group, PropertyMapping, User
from authentik.events.context_processors.base import get_context_processors
from authentik.events.utils import (
    cleanse_dict,
    get_user,
    model_to_dict,
    sanitize_dict,
    sanitize_item,
)
from authentik.lib.models import DomainlessURLValidator, SerializerModel
from authentik.lib.sentry import SentryIgnoredException
from authentik.lib.utils.errors import exception_to_dict
from authentik.lib.utils.http import get_http_session
from authentik.lib.utils.time import timedelta_from_string
from authentik.policies.models import PolicyBindingModel
from authentik.root.middleware import ClientIPMiddleware
from authentik.stages.email.utils import TemplateEmailMessage
from authentik.tasks.models import TasksModel
from authentik.tenants.models import Tenant
from authentik.tenants.utils import get_current_tenant

LOGGER = get_logger()
DISCORD_FIELD_LIMIT = 25
NOTIFICATION_SUMMARY_LENGTH = 75


def default_event_duration():
    """Default duration an Event is saved.
    This is used as a fallback when no brand is available"""
    try:
        tenant = get_current_tenant(only=["event_retention"])
        return now() + timedelta_from_string(tenant.event_retention)
    except Tenant.DoesNotExist:
        return now() + timedelta(days=365)


def default_brand():
    """Get a default value for brand"""
    return sanitize_dict(model_to_dict(DEFAULT_BRAND))


@lru_cache
def django_app_names() -> list[str]:
    """Get a cached list of all django apps' names (not labels)"""
    return [x.name for x in apps.app_configs.values()]


class NotificationTransportError(SentryIgnoredException):
    """Error raised when a notification fails to be delivered"""


class EventAction(models.TextChoices):
    """All possible actions to save into the events log"""

    LOGIN = "login"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"

    USER_WRITE = "user_write"
    SUSPICIOUS_REQUEST = "suspicious_request"
    PASSWORD_SET = "password_set"  # noqa # nosec

    SECRET_VIEW = "secret_view"  # noqa # nosec
    SECRET_ROTATE = "secret_rotate"  # noqa # nosec

    INVITE_USED = "invitation_used"

    AUTHORIZE_APPLICATION = "authorize_application"
    SOURCE_LINKED = "source_linked"

    IMPERSONATION_STARTED = "impersonation_started"
    IMPERSONATION_ENDED = "impersonation_ended"

    FLOW_EXECUTION = "flow_execution"
    POLICY_EXECUTION = "policy_execution"
    POLICY_EXCEPTION = "policy_exception"
    PROPERTY_MAPPING_EXCEPTION = "property_mapping_exception"

    SYSTEM_TASK_EXECUTION = "system_task_execution"
    SYSTEM_TASK_EXCEPTION = "system_task_exception"
    SYSTEM_EXCEPTION = "system_exception"

    CONFIGURATION_ERROR = "configuration_error"

    MODEL_CREATED = "model_created"
    MODEL_UPDATED = "model_updated"
    MODEL_DELETED = "model_deleted"
    EMAIL_SENT = "email_sent"

    UPDATE_AVAILABLE = "update_available"

    CUSTOM_PREFIX = "custom_"


class Event(SerializerModel, ExpiringModel):
    """An individual Audit/Metrics/Notification/Error Event"""

    event_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    user = models.JSONField(default=dict)
    action = models.TextField(choices=EventAction.choices)
    app = models.TextField()
    context = models.JSONField(default=dict, blank=True)
    client_ip = models.GenericIPAddressField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    brand = models.JSONField(default=default_brand, blank=True)

    # Shadow the expires attribute from ExpiringModel to override the default duration
    expires = models.DateTimeField(default=default_event_duration)

    @staticmethod
    def _get_app_from_request(request: HttpRequest) -> str:
        if not isinstance(request, HttpRequest):
            return ""
        return request.resolver_match.app_name

    @staticmethod
    def new(
        action: str | EventAction,
        app: str | None = None,
        **kwargs,
    ) -> "Event":
        """Create new Event instance from arguments. Instance is NOT saved."""
        if not isinstance(action, EventAction):
            action = EventAction.CUSTOM_PREFIX + action
        if not app:
            current = currentframe()
            parent = current.f_back
            app = parent.f_globals["__name__"]
            # Attempt to match the calling module to the django app it belongs to
            # if we can't find a match, keep the module name
            django_apps: list[str] = get_close_matches(app, django_app_names(), n=1)
            # Also ensure that closest django app has the correct prefix
            if len(django_apps) > 0 and django_apps[0].startswith(app):
                app = django_apps[0]
        cleaned_kwargs = cleanse_dict(sanitize_dict(kwargs))
        event = Event(action=action, app=app, context=cleaned_kwargs)
        return event

    def with_exception(self, exc: Exception) -> "Event":
        """Add data from 'exc' to the event in a database-saveable format"""
        self.context.setdefault("message", str(exc))
        self.context["exception"] = exception_to_dict(exc)
        return self

    def set_user(self, user: User) -> "Event":
        """Set `.user` based on user, ensuring the correct attributes are copied.
        This should only be used when self.from_http is *not* used."""
        self.user = get_user(user)
        return self

    def from_http(self, request: HttpRequest, user: User | None = None) -> "Event":
        """Add data from a Django-HttpRequest, allowing the creation of
        Events independently from requests.
        `user` arguments optionally overrides user from requests."""
        if request:
            from authentik.flows.views.executor import QS_QUERY

            self.context["http_request"] = {
                "path": request.path,
                "method": request.method,
                "args": cleanse_dict(QueryDict(request.META.get("QUERY_STRING", ""))),
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            }
            if hasattr(request, "request_id"):
                self.context["http_request"]["request_id"] = request.request_id
            # Special case for events created during flow execution
            # since they keep the http query within a wrapped query
            if QS_QUERY in self.context["http_request"]["args"]:
                wrapped = self.context["http_request"]["args"][QS_QUERY]
                self.context["http_request"]["args"] = cleanse_dict(QueryDict(wrapped))
        if hasattr(request, "brand"):
            brand: Brand = request.brand
            self.brand = sanitize_dict(model_to_dict(brand))
        if hasattr(request, "user"):
            self.user = get_user(request.user)
        if user:
            self.user = get_user(user)
        if hasattr(request, "session"):
            from authentik.flows.views.executor import SESSION_KEY_PLAN

            # Check if we're currently impersonating, and add that user
            if SESSION_KEY_IMPERSONATE_ORIGINAL_USER in request.session:
                self.user = get_user(request.session[SESSION_KEY_IMPERSONATE_ORIGINAL_USER])
                self.user["on_behalf_of"] = get_user(request.session[SESSION_KEY_IMPERSONATE_USER])
            # Special case for events that happen during a flow, the user might not be authenticated
            # yet but is a pending user instead
            if SESSION_KEY_PLAN in request.session:
                from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan

                plan: FlowPlan = request.session[SESSION_KEY_PLAN]
                pending_user = plan.context.get(PLAN_CONTEXT_PENDING_USER, None)
                # Only save `authenticated_as` if there's a different pending user in the flow
                # than the user that is authenticated
                if pending_user and (
                    (pending_user.pk and pending_user.pk != self.user.get("pk"))
                    or (not pending_user.pk)
                ):
                    orig_user = self.user.copy()

                    self.user = {"authenticated_as": orig_user, **get_user(pending_user)}
        # User 255.255.255.255 as fallback if IP cannot be determined
        self.client_ip = ClientIPMiddleware.get_client_ip(request)
        # Enrich event data
        for processor in get_context_processors():
            processor.enrich_event(self)
        # If there's no app set, we get it from the requests too
        if not self.app:
            self.app = Event._get_app_from_request(request)
        self.save()
        return self

    def save(self, *args, **kwargs):
        if self._state.adding:
            LOGGER.info(
                "Created Event",
                action=self.action,
                context=self.context,
                client_ip=self.client_ip,
                user=self.user,
            )
        super().save(*args, **kwargs)

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.events.api.events import EventSerializer

        return EventSerializer

    @property
    def summary(self) -> str:
        """Return a summary of this event."""
        if "message" in self.context:
            return self.context["message"]
        return f"{self.action}: {self.context}"

    def __str__(self) -> str:
        return f"Event action={self.action} user={self.user} context={self.context}"

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")
        indexes = ExpiringModel.Meta.indexes + [
            models.Index(fields=["action"]),
            models.Index(fields=["user"]),
            models.Index(fields=["app"]),
            models.Index(fields=["created"]),
            models.Index(fields=["client_ip"]),
            models.Index(
                models.F("context__authorized_application"),
                name="authentik_e_ctx_app__idx",
            ),
        ]


class TransportMode(models.TextChoices):
    """Modes that a notification transport can send a notification"""

    LOCAL = "local", _("authentik inbuilt notifications")
    WEBHOOK = "webhook", _("Generic Webhook")
    WEBHOOK_SLACK = "webhook_slack", _("Slack Webhook (Slack/Discord)")
    EMAIL = "email", _("Email")


class NotificationTransport(TasksModel, SerializerModel):
    """Action which is executed when a Rule matches"""

    uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    name = models.TextField(unique=True)
    mode = models.TextField(choices=TransportMode.choices, default=TransportMode.LOCAL)

    webhook_url = models.TextField(blank=True, validators=[DomainlessURLValidator()])
    webhook_mapping_body = models.ForeignKey(
        "NotificationWebhookMapping",
        on_delete=models.SET_DEFAULT,
        null=True,
        default=None,
        related_name="+",
        help_text=_(
            "Customize the body of the request. "
            "Mapping should return data that is JSON-serializable."
        ),
    )
    webhook_mapping_headers = models.ForeignKey(
        "NotificationWebhookMapping",
        on_delete=models.SET_DEFAULT,
        null=True,
        default=None,
        related_name="+",
        help_text=_(
            "Configure additional headers to be sent. "
            "Mapping should return a dictionary of key-value pairs"
        ),
    )
    send_once = models.BooleanField(
        default=False,
        help_text=_(
            "Only send notification once, for example when sending a webhook into a chat channel."
        ),
    )

    def send(self, notification: "Notification") -> list[str]:
        """Send notification to user, called from async task"""
        if self.mode == TransportMode.LOCAL:
            return self.send_local(notification)
        if self.mode == TransportMode.WEBHOOK:
            return self.send_webhook(notification)
        if self.mode == TransportMode.WEBHOOK_SLACK:
            return self.send_webhook_slack(notification)
        if self.mode == TransportMode.EMAIL:
            return self.send_email(notification)
        raise ValueError(f"Invalid mode {self.mode} set")

    def send_local(self, notification: "Notification") -> list[str]:
        """Local notification delivery"""
        if self.webhook_mapping_body:
            self.webhook_mapping_body.evaluate(
                user=notification.user,
                request=None,
                notification=notification,
            )
        notification.save()
        return []

    def send_webhook(self, notification: "Notification") -> list[str]:
        """Send notification to generic webhook"""
        default_body = {
            "body": notification.body,
            "severity": notification.severity,
            "user_email": notification.user.email,
            "user_username": notification.user.username,
        }
        if notification.event and notification.event.user:
            default_body["event_user_email"] = notification.event.user.get("email", None)
            default_body["event_user_username"] = notification.event.user.get("username", None)
        headers = {}
        if self.webhook_mapping_body:
            default_body = sanitize_item(
                self.webhook_mapping_body.evaluate(
                    user=notification.user,
                    request=None,
                    notification=notification,
                )
            )
        if self.webhook_mapping_headers:
            headers = sanitize_item(
                self.webhook_mapping_headers.evaluate(
                    user=notification.user,
                    request=None,
                    notification=notification,
                )
            )
        try:
            response = get_http_session().post(
                self.webhook_url,
                json=default_body,
                headers=headers,
            )
            response.raise_for_status()
        except RequestException as exc:
            raise NotificationTransportError(
                exc.response.text if exc.response else str(exc)
            ) from exc
        return [
            response.status_code,
            response.text,
        ]

    def send_webhook_slack(self, notification: "Notification") -> list[str]:
        """Send notification to slack or slack-compatible endpoints"""
        fields = [
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
        ]
        if notification.event:
            if notification.event.user:
                fields.append(
                    {
                        "title": _("Event user"),
                        "value": str(notification.event.user.get("username")),
                        "short": True,
                    },
                )
            for key, value in notification.event.context.items():
                if not isinstance(value, str):
                    continue
                # https://birdie0.github.io/discord-webhooks-guide/other/field_limits.html
                if len(fields) >= DISCORD_FIELD_LIMIT:
                    continue
                fields.append({"title": key[:256], "value": value[:1024]})
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
                    "fields": fields,
                    "footer": f"authentik {get_full_version()}",
                }
            ],
        }
        if notification.event:
            body["attachments"][0]["title"] = notification.event.action
        try:
            response = get_http_session().post(self.webhook_url, json=body)
            response.raise_for_status()
        except RequestException as exc:
            text = exc.response.text if exc.response else str(exc)
            raise NotificationTransportError(text) from exc
        return [
            response.status_code,
            response.text,
        ]

    def send_email(self, notification: "Notification") -> list[str]:
        """Send notification via global email configuration"""
        from authentik.stages.email.tasks import send_mail

        if notification.user.email.strip() == "":
            LOGGER.info(
                "Discarding notification as user has no email address",
                user=notification.user,
                notification=notification,
            )
            return None
        subject_prefix = "authentik Notification: "
        context = {
            "key_value": {
                "user_email": notification.user.email,
                "user_username": notification.user.username,
            },
            "body": notification.body,
            "title": "",
        }
        if notification.event and notification.event.user:
            context["key_value"]["event_user_email"] = notification.event.user.get("email", None)
            context["key_value"]["event_user_username"] = notification.event.user.get(
                "username", None
            )
        if notification.event:
            context["title"] += notification.event.action
            for key, value in notification.event.context.items():
                if not isinstance(value, str):
                    continue
                context["key_value"][key] = value
        else:
            context["title"] += notification.body[:NOTIFICATION_SUMMARY_LENGTH]
        # TODO: improve permission check
        if notification.user.is_superuser:
            context["source"] = {
                "from": self.name,
            }
        mail = TemplateEmailMessage(
            subject=subject_prefix + context["title"],
            to=[(notification.user.name, notification.user.email)],
            language=notification.user.locale(),
            template_name="email/event_notification.html",
            template_context=context,
        )
        send_mail.send_with_options(args=(mail.__dict__,), rel_obj=self)
        return []

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.events.api.notification_transports import (
            NotificationTransportSerializer,
        )

        return NotificationTransportSerializer

    def __str__(self) -> str:
        return f"Notification Transport {self.name}"

    class Meta:
        verbose_name = _("Notification Transport")
        verbose_name_plural = _("Notification Transports")


class NotificationSeverity(models.TextChoices):
    """Severity images that a notification can have"""

    NOTICE = "notice", _("Notice")
    WARNING = "warning", _("Warning")
    ALERT = "alert", _("Alert")


class Notification(SerializerModel):
    """Event Notification"""

    uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    severity = models.TextField(choices=NotificationSeverity.choices)
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True)
    seen = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.events.api.notifications import NotificationSerializer

        return NotificationSerializer

    def __str__(self) -> str:
        body_trunc = (
            (self.body[:NOTIFICATION_SUMMARY_LENGTH] + "..")
            if len(self.body) > NOTIFICATION_SUMMARY_LENGTH
            else self.body
        )
        return f"Notification for user {self.user_id}: {body_trunc}"

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")


class NotificationRule(TasksModel, SerializerModel, PolicyBindingModel):
    """Decide when to create a Notification based on policies attached to this object."""

    name = models.TextField(unique=True)
    transports = models.ManyToManyField(
        NotificationTransport,
        help_text=_(
            "Select which transports should be used to notify the user. If none are "
            "selected, the notification will only be shown in the authentik UI."
        ),
        blank=True,
    )
    severity = models.TextField(
        choices=NotificationSeverity.choices,
        default=NotificationSeverity.NOTICE,
        help_text=_("Controls which severity level the created notifications will have."),
    )
    destination_group = models.ForeignKey(
        Group,
        help_text=_(
            "Define which group of users this notification should be sent and shown to. "
            "If left empty, Notification won't ben sent."
        ),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    destination_event_user = models.BooleanField(
        default=False,
        help_text=_(
            "When enabled, notification will be sent to user the user that triggered the event."
            "When destination_group is configured, notification is sent to both."
        ),
    )

    def destination_users(self, event: Event) -> Generator[User, Any]:
        if self.destination_event_user and event.user.get("pk"):
            yield User(pk=event.user.get("pk"))
        if self.destination_group:
            yield from self.destination_group.users.all()

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.events.api.notification_rules import NotificationRuleSerializer

        return NotificationRuleSerializer

    def __str__(self) -> str:
        return f"Notification Rule {self.name}"

    class Meta:
        verbose_name = _("Notification Rule")
        verbose_name_plural = _("Notification Rules")


class NotificationWebhookMapping(PropertyMapping):
    """Modify the payload of outgoing webhook requests"""

    @property
    def component(self) -> str:
        return "ak-property-mapping-notification-form"

    @property
    def serializer(self) -> type[type[Serializer]]:
        from authentik.events.api.notification_mappings import (
            NotificationWebhookMappingSerializer,
        )

        return NotificationWebhookMappingSerializer

    def __str__(self):
        return f"Webhook Mapping {self.name}"

    class Meta:
        verbose_name = _("Webhook Mapping")
        verbose_name_plural = _("Webhook Mappings")


class TaskStatus(models.TextChoices):
    """DEPRECATED do not use"""

    UNKNOWN = "unknown"
    SUCCESSFUL = "successful"
    WARNING = "warning"
    ERROR = "error"


class SystemTask(ExpiringModel):
    """DEPRECATED do not use"""

    uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    name = models.TextField()
    uid = models.TextField(null=True)

    start_timestamp = models.DateTimeField(default=now)
    finish_timestamp = models.DateTimeField(default=now)
    duration = models.FloatField(default=0)

    status = models.TextField(choices=TaskStatus.choices)

    description = models.TextField(null=True)
    messages = models.JSONField()

    task_call_module = models.TextField()
    task_call_func = models.TextField()
    task_call_args = models.JSONField(default=list)
    task_call_kwargs = models.JSONField(default=dict)

    def __str__(self) -> str:
        return f"System Task {self.name}"

    class Meta:
        unique_together = (("name", "uid"),)
        default_permissions = ()
        permissions = ()
        verbose_name = _("System Task")
        verbose_name_plural = _("System Tasks")
        indexes = ExpiringModel.Meta.indexes
