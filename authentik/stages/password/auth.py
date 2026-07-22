"""Password-stage authentication orchestration."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from django.contrib.auth import _clean_credentials
from django.contrib.auth.backends import BaseBackend
from django.http import HttpRequest
from sentry_sdk import start_span
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.core.signals import login_failed
from authentik.flows.models import Stage
from authentik.lib.utils.reflection import path_to_class
from authentik.stages.password.models import PasswordStage

LOGGER = get_logger()


class PasswordAuthenticationStatus(Enum):
    """Outcome of password authentication after applying optional policy extensions."""

    AUTHENTICATED = auto()
    INVALID = auto()
    LAST_ATTEMPT = auto()
    LOCKED = auto()


@dataclass(frozen=True)
class PasswordAuthenticationResult:
    """Authenticated user and the resulting lockout-policy status."""

    status: PasswordAuthenticationStatus
    user: User | None = None


def authenticate(
    request: HttpRequest,
    backends: list[str],
    stage: Stage | None = None,
    **credentials: Any,
) -> User | None:
    """Authenticate credentials against the selected backends."""
    for backend_path in backends:
        try:
            backend: BaseBackend = path_to_class(backend_path)()
        except ImportError:
            LOGGER.warning("Failed to import backend", path=backend_path)
            continue
        LOGGER.debug("Attempting authentication...", backend=backend_path)
        with start_span(
            op="authentik.stages.password.authenticate",
            name=backend_path,
        ):
            user = backend.authenticate(request, **credentials)
        if user is None:
            LOGGER.debug("Backend returned nothing, continuing", backend=backend_path)
            continue
        user.backend = backend_path
        LOGGER.info("Successful authentication", user=user.username, backend=backend_path)
        return user

    login_failed.send(
        sender=__name__,
        credentials=_clean_credentials(credentials),
        request=request,
        stage=stage,
    )
    return None


def authenticate_password(
    request: HttpRequest,
    password_stage: PasswordStage,
    pending_user: User,
    password: str | None,
    event_stage: Stage,
) -> PasswordAuthenticationResult:
    """Authenticate a password, applying the Enterprise lockout policy when available."""
    try:
        from authentik.enterprise.stages.password.lockout import (
            authenticate_password as authenticate_password_with_lockout,
        )
    except ModuleNotFoundError:
        authenticate_password_with_lockout = None
    if authenticate_password_with_lockout is not None:
        return authenticate_password_with_lockout(
            request,
            password_stage,
            pending_user,
            password,
            event_stage,
        )
    user = authenticate(
        request,
        password_stage.backends,
        event_stage,
        username=pending_user.username,
        password=password,
    )
    return PasswordAuthenticationResult(
        (
            PasswordAuthenticationStatus.AUTHENTICATED
            if user
            else PasswordAuthenticationStatus.INVALID
        ),
        user,
    )
