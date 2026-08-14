"""authentik core signals"""

from contextlib import contextmanager
from contextvars import ContextVar

from channels.layers import get_channel_layer
from django.contrib.auth.signals import user_logged_in
from django.core.cache import cache
from django.db.models import Model
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import Signal, receiver
from django.http.request import HttpRequest
from structlog.stdlib import get_logger

from authentik.core.models import (
    Application,
    AuthenticatedSession,
    BackchannelProvider,
    Session,
    User,
    default_token_duration,
)
from authentik.flows.apps import RefreshOtherFlowsAfterAuthentication
from authentik.lib.models import ExpiringModel
from authentik.root.ws.consumer import build_device_group

password_changed = Signal()
"""Arguments: user: User, password: str"""
password_hash_changed = Signal()
"""Arguments: user: User, request: HttpRequest | None"""
login_failed = Signal()
"""Arguments: credentials: dict[str, any], request: HttpRequest,
stage: Stage, context: dict[str, any]"""
admin_authenticated_session_deleted = Signal()
"""Arguments: instance: AuthenticatedSession, request: HttpRequest"""

LOGGER = get_logger()

_CTX_INHIBIT_DEACTIVATION_SESSION_CLEANUP = ContextVar[bool](
    "authentik_core_inhibit_deactivation_session_cleanup",
    default=False,
)
_CTX_INHIBIT_DEACTIVATION_TOKEN_CLEANUP = ContextVar[bool](
    "authentik_core_inhibit_deactivation_token_cleanup",
    default=False,
)


@contextmanager
def deactivation_inhibit_cleanup(*, sessions: bool = True, tokens: bool = True):
    """
    Prevent the automatic cleanup that runs when a deactivated user is saved,
    for callers that revoke sessions and/or tokens themselves (e.g. enterprise
    revocation). `sessions` inhibits session deletion, `tokens` inhibits
    provider token revocation; both are inhibited by default. Nested uses can
    add inhibition but not remove the outer context's.
    """
    reset_sessions = _CTX_INHIBIT_DEACTIVATION_SESSION_CLEANUP.set(
        _CTX_INHIBIT_DEACTIVATION_SESSION_CLEANUP.get() or sessions
    )
    reset_tokens = _CTX_INHIBIT_DEACTIVATION_TOKEN_CLEANUP.set(
        _CTX_INHIBIT_DEACTIVATION_TOKEN_CLEANUP.get() or tokens
    )
    try:
        yield
    finally:
        _CTX_INHIBIT_DEACTIVATION_SESSION_CLEANUP.reset(reset_sessions)
        _CTX_INHIBIT_DEACTIVATION_TOKEN_CLEANUP.reset(reset_tokens)


def deactivation_session_cleanup_inhibited() -> bool:
    """Whether deactivation session cleanup is inhibited in the current context"""
    return _CTX_INHIBIT_DEACTIVATION_SESSION_CLEANUP.get()


def deactivation_token_cleanup_inhibited() -> bool:
    """Whether deactivation token cleanup is inhibited in the current context"""
    return _CTX_INHIBIT_DEACTIVATION_TOKEN_CLEANUP.get()


@receiver(post_save, sender=Application)
def post_save_application(sender: type[Model], instance, created: bool, **_):
    """Clear user's application cache upon application creation"""
    from authentik.core.api.applications import user_app_cache_key

    if not created:  # pragma: no cover
        return

    # Also delete user application cache
    keys = cache.keys(user_app_cache_key("*"))
    cache.delete_many(keys)


@receiver(user_logged_in)
def user_logged_in_session(sender, request: HttpRequest, user: User, **_):
    """Create an AuthenticatedSession from request"""

    AuthenticatedSession.create_from_request(request, user)

    if not RefreshOtherFlowsAfterAuthentication.get():
        return
    layer = get_channel_layer()
    device_cookie = request.COOKIES.get("authentik_device")
    if device_cookie:
        layer.group_send_blocking(
            build_device_group(device_cookie),
            {"type": "event.session.authenticated"},
        )


@receiver(post_save, sender=User)
def user_deactivated_delete_sessions(sender: type[Model], instance: User, **_):
    """Delete all of a user's sessions when they are deactivated"""
    if instance.is_active:
        return
    if deactivation_session_cleanup_inhibited():
        return
    Session.objects.filter(authenticatedsession__user=instance).delete()
    LOGGER.debug("Deleted deactivated user's sessions", user=instance.username)


@receiver(post_delete, sender=AuthenticatedSession)
def authenticated_session_delete(sender: type[Model], instance: AuthenticatedSession, **_):
    """Delete session when authenticated session is deleted"""
    Session.objects.filter(session_key=instance.pk).delete()


@receiver(pre_save)
def backchannel_provider_pre_save(sender: type[Model], instance: Model, **_):
    """Ensure backchannel providers have is_backchannel set to true"""
    if not isinstance(instance, BackchannelProvider):
        return
    instance.is_backchannel = True


@receiver(pre_save)
def expiring_model_pre_save(sender: type[Model], instance: Model, **_):
    """Ensure expires is set on ExpiringModels that are set to expire"""
    if not issubclass(sender, ExpiringModel):
        return
    if instance.expiring and instance.expires is None:
        instance.expires = default_token_duration()
