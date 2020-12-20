"""authentik events models"""
from dataclasses import asdict, is_dataclass
from inspect import getmodule, stack
from typing import Any, Dict, Optional, Union
from uuid import UUID, uuid4

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.base import Model
from django.http import HttpRequest
from django.utils.translation import gettext as _
from django.views.debug import SafeExceptionReporterFilter
from guardian.utils import get_anonymous_user
from structlog import get_logger

from authentik.core.middleware import (
    SESSION_IMPERSONATE_ORIGINAL_USER,
    SESSION_IMPERSONATE_USER,
)
from authentik.core.models import User
from authentik.lib.utils.http import get_client_ip

LOGGER = get_logger("authentik.events")


def cleanse_dict(source: Dict[Any, Any]) -> Dict[Any, Any]:
    """Cleanse a dictionary, recursively"""
    final_dict = {}
    for key, value in source.items():
        try:
            if SafeExceptionReporterFilter.hidden_settings.search(key):
                final_dict[key] = SafeExceptionReporterFilter.cleansed_substitute
            else:
                final_dict[key] = value
        except TypeError:
            final_dict[key] = value
        if isinstance(value, dict):
            final_dict[key] = cleanse_dict(value)
    return final_dict


def model_to_dict(model: Model) -> Dict[str, Any]:
    """Convert model to dict"""
    name = str(model)
    if hasattr(model, "name"):
        name = model.name
    return {
        "app": model._meta.app_label,
        "model_name": model._meta.model_name,
        "pk": model.pk,
        "name": name,
    }


def get_user(user: User, original_user: Optional[User] = None) -> Dict[str, Any]:
    """Convert user object to dictionary, optionally including the original user"""
    if isinstance(user, AnonymousUser):
        user = get_anonymous_user()
    user_data = {
        "username": user.username,
        "pk": user.pk,
        "email": user.email,
    }
    if original_user:
        original_data = get_user(original_user)
        original_data["on_behalf_of"] = user_data
        return original_data
    return user_data


def sanitize_dict(source: Dict[Any, Any]) -> Dict[Any, Any]:
    """clean source of all Models that would interfere with the JSONField.
    Models are replaced with a dictionary of {
        app: str,
        name: str,
        pk: Any
    }"""
    final_dict = {}
    for key, value in source.items():
        if is_dataclass(value):
            value = asdict(value)
        if isinstance(value, dict):
            final_dict[key] = sanitize_dict(value)
        elif isinstance(value, models.Model):
            final_dict[key] = sanitize_dict(model_to_dict(value))
        elif isinstance(value, UUID):
            final_dict[key] = value.hex
        else:
            final_dict[key] = value
    return final_dict


class EventAction(models.TextChoices):
    """All possible actions to save into the events log"""

    LOGIN = "login"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"

    USER_WRITE = "user_write"
    SUSPICIOUS_REQUEST = "suspicious_request"
    PASSWORD_SET = "password_set"  # noqa # nosec

    TOKEN_VIEW = "token_view"  # nosec

    INVITE_CREATED = "invitation_created"
    INVITE_USED = "invitation_used"

    AUTHORIZE_APPLICATION = "authorize_application"
    SOURCE_LINKED = "source_linked"

    IMPERSONATION_STARTED = "impersonation_started"
    IMPERSONATION_ENDED = "impersonation_ended"

    POLICY_EXECUTION = "policy_execution"
    POLICY_EXCEPTION = "policy_exception"
    PROPERTY_MAPPING_EXCEPTION = "property_mapping_exception"

    MODEL_CREATED = "model_created"
    MODEL_UPDATED = "model_updated"
    MODEL_DELETED = "model_deleted"

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

    def from_http(
        self, request: HttpRequest, user: Optional[settings.AUTH_USER_MODEL] = None
    ) -> "Event":
        """Add data from a Django-HttpRequest, allowing the creation of
        Events independently from requests.
        `user` arguments optionally overrides user from requests."""
        if hasattr(request, "user"):
            self.user = get_user(
                request.user,
                request.session.get(SESSION_IMPERSONATE_ORIGINAL_USER, None),
            )
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

    class Meta:

        verbose_name = _("Event")
        verbose_name_plural = _("Events")
