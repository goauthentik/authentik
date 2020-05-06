"""passbook audit models"""
from enum import Enum
from inspect import getmodule, stack
from typing import Any, Dict, Optional
from uuid import UUID

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.http import HttpRequest
from django.utils.translation import gettext as _
from guardian.shortcuts import get_anonymous_user
from structlog import get_logger

from passbook.lib.models import UUIDModel
from passbook.lib.utils.http import get_client_ip

LOGGER = get_logger()


def sanitize_dict(source: Dict[Any, Any]) -> Dict[Any, Any]:
    """clean source of all Models that would interfere with the JSONField.
    Models are replaced with a dictionary of {
        app: str,
        name: str,
        pk: Any
    }"""
    for key, value in source.items():
        if isinstance(value, dict):
            source[key] = sanitize_dict(value)
        elif isinstance(value, models.Model):
            model_content_type = ContentType.objects.get_for_model(value)
            name = str(value)
            if hasattr(value, "name"):
                name = value.name
            source[key] = sanitize_dict(
                {
                    "app": model_content_type.app_label,
                    "model_name": model_content_type.model,
                    "pk": value.pk,
                    "name": name,
                }
            )
        elif isinstance(value, UUID):
            source[key] = value.hex
    return source


class EventAction(Enum):
    """All possible actions to save into the audit log"""

    LOGIN = "login"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    AUTHORIZE_APPLICATION = "authorize_application"
    SUSPICIOUS_REQUEST = "suspicious_request"
    SIGN_UP = "sign_up"
    PASSWORD_RESET = "password_reset"  # noqa # nosec
    INVITE_CREATED = "invitation_created"
    INVITE_USED = "invitation_used"
    CUSTOM = "custom"

    @staticmethod
    def as_choices():
        """Generate choices of actions used for database"""
        return tuple(
            (x, y.value) for x, y in getattr(EventAction, "__members__").items()
        )


class Event(UUIDModel):
    """An individual audit log event"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    action = models.TextField(choices=EventAction.as_choices())
    date = models.DateTimeField(auto_now_add=True)
    app = models.TextField()
    context = JSONField(default=dict, blank=True)
    client_ip = models.GenericIPAddressField(null=True)
    created = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def _get_app_from_request(request: HttpRequest) -> str:
        if not isinstance(request, HttpRequest):
            return ""
        return request.resolver_match.app_name

    @staticmethod
    def new(
        action: EventAction,
        app: Optional[str] = None,
        _inspect_offset: int = 1,
        **kwargs,
    ) -> "Event":
        """Create new Event instance from arguments. Instance is NOT saved."""
        if not isinstance(action, EventAction):
            raise ValueError(
                f"action must be EventAction instance but was {type(action)}"
            )
        if not app:
            app = getmodule(stack()[_inspect_offset][0]).__name__
        cleaned_kwargs = sanitize_dict(kwargs)
        event = Event(action=action.value, app=app, context=cleaned_kwargs)
        return event

    def from_http(
        self, request: HttpRequest, user: Optional[settings.AUTH_USER_MODEL] = None
    ) -> "Event":
        """Add data from a Django-HttpRequest, allowing the creation of
        Events independently from requests.
        `user` arguments optionally overrides user from requests."""
        if hasattr(request, "user"):
            if isinstance(request.user, AnonymousUser):
                self.user = get_anonymous_user()
            else:
                self.user = request.user
        if user:
            self.user = user
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
            "Created Audit event",
            action=self.action,
            context=self.context,
            client_ip=self.client_ip,
            user=self.user,
        )
        return super().save(*args, **kwargs)

    class Meta:

        verbose_name = _("Audit Event")
        verbose_name_plural = _("Audit Events")
