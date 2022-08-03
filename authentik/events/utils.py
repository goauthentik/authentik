"""event utilities"""
import re
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from django.contrib.auth.models import AnonymousUser
from django.core.handlers.wsgi import WSGIRequest
from django.db import models
from django.db.models.base import Model
from django.http.request import HttpRequest
from django.views.debug import SafeExceptionReporterFilter
from geoip2.models import City
from guardian.utils import get_anonymous_user

from authentik.core.models import User
from authentik.events.geo import GEOIP_READER
from authentik.policies.types import PolicyRequest

# Special keys which are *not* cleaned, even when the default filter
# is matched
ALLOWED_SPECIAL_KEYS = re.compile("passing", flags=re.I)


def cleanse_dict(source: dict[Any, Any]) -> dict[Any, Any]:
    """Cleanse a dictionary, recursively"""
    final_dict = {}
    for key, value in source.items():
        try:
            if SafeExceptionReporterFilter.hidden_settings.search(
                key
            ) and not ALLOWED_SPECIAL_KEYS.search(key):
                final_dict[key] = SafeExceptionReporterFilter.cleansed_substitute
            else:
                final_dict[key] = value
        except TypeError:  # pragma: no cover
            final_dict[key] = value
        if isinstance(value, dict):
            final_dict[key] = cleanse_dict(value)
    return final_dict


def model_to_dict(model: Model) -> dict[str, Any]:
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


def get_user(user: User, original_user: Optional[User] = None) -> dict[str, Any]:
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


def sanitize_dict(source: dict[Any, Any]) -> dict[Any, Any]:
    """clean source of all Models that would interfere with the JSONField.
    Models are replaced with a dictionary of {
        app: str,
        name: str,
        pk: Any
    }"""
    final_dict = {}
    for key, value in source.items():
        if is_dataclass(value):
            # Because asdict calls `copy.deepcopy(obj)` on everything that's not tuple/dict,
            # and deepcopy doesn't work with HttpRequests (neither django nor rest_framework).
            # Currently, the only dataclass that actually holds an http request is a PolicyRequest
            if isinstance(value, PolicyRequest):
                value.http_request = None
            value = asdict(value)
        if isinstance(value, dict):
            final_dict[key] = sanitize_dict(value)
        elif isinstance(value, (User, AnonymousUser)):
            final_dict[key] = sanitize_dict(get_user(value))
        elif isinstance(value, models.Model):
            final_dict[key] = sanitize_dict(model_to_dict(value))
        elif isinstance(value, UUID):
            final_dict[key] = value.hex
        elif isinstance(value, (HttpRequest, WSGIRequest)):
            continue
        elif isinstance(value, City):
            final_dict[key] = GEOIP_READER.city_to_dict(value)
        elif isinstance(value, Path):
            final_dict[key] = str(value)
        elif isinstance(value, type):
            final_dict[key] = {
                "type": value.__name__,
                "module": value.__module__,
            }
        else:
            final_dict[key] = value
    return final_dict
