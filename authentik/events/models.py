"""authentik events models"""
import time
from collections import Counter
from datetime import timedelta
from inspect import currentframe
from smtplib import SMTPException
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from django.db import models
from django.db.models import Count, ExpressionWrapper, F
from django.db.models.fields import DurationField
from django.db.models.functions import Extract
from django.db.models.manager import Manager
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.http.request import QueryDict
from django.utils.timezone import now
from django.utils.translation import gettext as _
from requests import RequestException
from structlog.stdlib import get_logger

from authentik import get_full_version
from authentik.core.middleware import (
    SESSION_KEY_IMPERSONATE_ORIGINAL_USER,
    SESSION_KEY_IMPERSONATE_USER,
)
from authentik.core.models import ExpiringModel, Group, PropertyMapping, User
from authentik.events.geo import GEOIP_READER
from authentik.events.utils import (
    cleanse_dict,
    get_user,
    model_to_dict,
    sanitize_dict,
    sanitize_item,
)
from authentik.lib.models import DomainlessURLValidator, SerializerModel
from authentik.lib.sentry import SentryIgnoredException
from authentik.lib.utils.http import get_client_ip, get_http_session
from authentik.lib.utils.time import timedelta_from_string
from authentik.policies.models import PolicyBindingModel
from authentik.stages.email.utils import TemplateEmailMessage
from authentik.tenants.models import Tenant
from authentik.tenants.utils import DEFAULT_TENANT

LOGGER = get_logger()
if TYPE_CHECKING:
    from rest_framework.serializers import Serializer


def default_event_duration():
    """Default duration an Event is saved.
    This is used as a fallback when no tenant is available"""
    return now() + timedelta(days=365)


def default_tenant():
    """Get a default value for tenant"""
    return sanitize_dict(model_to_dict(DEFAULT_TENANT))


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


class EventQuerySet(QuerySet):
    """Custom events query set with helper functions"""

    def get_events_per(
        self,
        time_since: timedelta,
        extract: Extract,
        data_points: int,
    ) -> list[dict[str, int]]:
        """Get event count by hour in the last day, fill with zeros"""
        _now = now()
        max_since = timedelta(days=60)
        # Allow maximum of 60 days to limit load
        if time_since.total_seconds() > max_since.total_seconds():
            time_since = max_since
        date_from = _now - time_since
        result = (
            self.filter(created__gte=date_from)
            .annotate(age=ExpressionWrapper(_now - F("created"), output_field=DurationField()))
            .annotate(age_interval=extract("age"))
            .values("age_interval")
            .annotate(count=Count("pk"))
            .order_by("age_interval")
        )
        data = Counter({int(d["age_interval"]): d["count"] for d in result})
        results = []
        interval_delta = time_since / data_points
        for interval in range(1, -data_points, -1):
            results.append(
                {
                    "x_cord": time.mktime((_now + (interval_delta * interval)).timetuple()) * 1000,
                    "y_cord": data[interval * -1],
                }
            )
        return results


class EventManager(Manager):
    """Custom helper methods for Events"""

    def get_queryset(self) -> QuerySet:
        """use custom queryset"""
        return EventQuerySet(self.model, using=self._db)

    def get_events_per(
        self,
        time_since: timedelta,
        extract: Extract,
        data_points: int,
    ) -> list[dict[str, int]]:
        """Wrap method from queryset"""
        return self.get_queryset().get_events_per(time_since, extract, data_points)


class Event(SerializerModel, ExpiringModel):
    """An individual Audit/Metrics/Notification/Error Event"""

    event_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    user = models.JSONField(default=dict)
    action = models.TextField(choices=EventAction.choices)
    app = models.TextField()
    context = models.JSONField(default=dict, blank=True)
    client_ip = models.GenericIPAddressField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    tenant = models.JSONField(default=default_tenant, blank=True)

    # Shadow the expires attribute from ExpiringModel to override the default duration
    expires = models.DateTimeField(default=default_event_duration)

    objects = EventManager()

    @staticmethod
    def _get_app_from_request(request: HttpRequest) -> str:
        if not isinstance(request, HttpRequest):
            return ""
        return request.resolver_match.app_name

    @staticmethod
    def new(
        action: str | EventAction,
        app: Optional[str] = None,
        **kwargs,
    ) -> "Event":
        """Create new Event instance from arguments. Instance is NOT saved."""
        if not isinstance(action, EventAction):
            action = EventAction.CUSTOM_PREFIX + action
        if not app:
            current = currentframe()
            parent = current.f_back
            app = parent.f_globals["__name__"]
        cleaned_kwargs = cleanse_dict(sanitize_dict(kwargs))
        event = Event(action=action, app=app, context=cleaned_kwargs)
        return event

    def set_user(self, user: User) -> "Event":
        """Set `.user` based on user, ensuring the correct attributes are copied.
        This should only be used when self.from_http is *not* used."""
        self.user = get_user(user)
        return self

    def from_http(self, request: HttpRequest, user: Optional[User] = None) -> "Event":
        """Add data from a Django-HttpRequest, allowing the creation of
        Events independently from requests.
        `user` arguments optionally overrides user from requests."""
        if request:
            from authentik.flows.views.executor import QS_QUERY

            self.context["http_request"] = {
                "path": request.path,
                "method": request.method,
                "args": cleanse_dict(QueryDict(request.META.get("QUERY_STRING", ""))),
            }
            # Special case for events created during flow execution
            # since they keep the http query within a wrapped query
            if QS_QUERY in self.context["http_request"]["args"]:
                wrapped = self.context["http_request"]["args"][QS_QUERY]
                self.context["http_request"]["args"] = cleanse_dict(QueryDict(wrapped))
        if hasattr(request, "tenant"):
            tenant: Tenant = request.tenant
            # Because self.created only gets set on save, we can't use it's value here
            # hence we set self.created to now and then use it
            self.created = now()
            self.expires = self.created + timedelta_from_string(tenant.event_retention)
            self.tenant = sanitize_dict(model_to_dict(tenant))
        if hasattr(request, "user"):
            original_user = None
            if hasattr(request, "session"):
                original_user = request.session.get(SESSION_KEY_IMPERSONATE_ORIGINAL_USER, None)
            self.user = get_user(request.user, original_user)
        if user:
            self.user = get_user(user)
        # Check if we're currently impersonating, and add that user
        if hasattr(request, "session"):
            if SESSION_KEY_IMPERSONATE_ORIGINAL_USER in request.session:
                self.user = get_user(request.session[SESSION_KEY_IMPERSONATE_ORIGINAL_USER])
                self.user["on_behalf_of"] = get_user(request.session[SESSION_KEY_IMPERSONATE_USER])
        # User 255.255.255.255 as fallback if IP cannot be determined
        self.client_ip = get_client_ip(request)
        # Apply GeoIP Data, when enabled
        self.with_geoip()
        # If there's no app set, we get it from the requests too
        if not self.app:
            self.app = Event._get_app_from_request(request)
        self.save()
        return self

    def with_geoip(self):  # pragma: no cover
        """Apply GeoIP Data, when enabled"""
        city = GEOIP_READER.city_dict(self.client_ip)
        if not city:
            return
        self.context["geo"] = city

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
    def serializer(self) -> "Serializer":
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


class TransportMode(models.TextChoices):
    """Modes that a notification transport can send a notification"""

    LOCAL = "local", _("authentik inbuilt notifications")
    WEBHOOK = "webhook", _("Generic Webhook")
    WEBHOOK_SLACK = "webhook_slack", _("Slack Webhook (Slack/Discord)")
    EMAIL = "email", _("Email")


class NotificationTransport(SerializerModel):
    """Action which is executed when a Rule matches"""

    uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    name = models.TextField(unique=True)
    mode = models.TextField(choices=TransportMode.choices, default=TransportMode.LOCAL)

    webhook_url = models.TextField(blank=True, validators=[DomainlessURLValidator()])
    webhook_mapping = models.ForeignKey(
        "NotificationWebhookMapping", on_delete=models.SET_DEFAULT, null=True, default=None
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
        if self.webhook_mapping:
            self.webhook_mapping.evaluate(
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
        if self.webhook_mapping:
            default_body = sanitize_item(
                self.webhook_mapping.evaluate(
                    user=notification.user,
                    request=None,
                    notification=notification,
                )
            )
        try:
            response = get_http_session().post(
                self.webhook_url,
                json=default_body,
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
                if len(fields) >= 25:
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
            context["title"] += notification.body[:75]
        # TODO: improve permission check
        if notification.user.is_superuser:
            context["source"] = {
                "from": self.name,
            }
        mail = TemplateEmailMessage(
            subject=subject_prefix + context["title"],
            to=[notification.user.email],
            language=notification.user.locale(),
            template_name="email/event_notification.html",
            template_context=context,
        )
        # Email is sent directly here, as the call to send() should have been from a task.
        try:
            from authentik.stages.email.tasks import send_mail

            return send_mail(mail.__dict__)  # pylint: disable=no-value-for-parameter
        except (SMTPException, ConnectionError, OSError) as exc:
            raise NotificationTransportError(exc) from exc

    @property
    def serializer(self) -> "Serializer":
        from authentik.events.api.notification_transports import NotificationTransportSerializer

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
    def serializer(self) -> "Serializer":
        from authentik.events.api.notifications import NotificationSerializer

        return NotificationSerializer

    def __str__(self) -> str:
        body_trunc = (self.body[:75] + "..") if len(self.body) > 75 else self.body
        return f"Notification for user {self.user}: {body_trunc}"

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")


class NotificationRule(SerializerModel, PolicyBindingModel):
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
    group = models.ForeignKey(
        Group,
        help_text=_(
            "Define which group of users this notification should be sent and shown to. "
            "If left empty, Notification won't ben sent."
        ),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    @property
    def serializer(self) -> "Serializer":
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
    def serializer(self) -> type["Serializer"]:
        from authentik.events.api.notification_mappings import NotificationWebhookMappingSerializer

        return NotificationWebhookMappingSerializer

    def __str__(self):
        return f"Webhook Mapping {self.name}"

    class Meta:
        verbose_name = _("Webhook Mapping")
        verbose_name_plural = _("Webhook Mappings")
