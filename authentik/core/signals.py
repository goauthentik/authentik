"""authentik core signals"""
from typing import TYPE_CHECKING

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.sessions.backends.cache import KEY_PREFIX
from django.core.cache import cache
from django.core.signals import Signal
from django.db.models import Model
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.http.request import HttpRequest

# Arguments: user: User, password: str
password_changed = Signal()

if TYPE_CHECKING:
    from authentik.core.models import AuthenticatedSession, User


@receiver(post_save)
# pylint: disable=unused-argument
def post_save_application(sender: type[Model], instance, created: bool, **_):
    """Clear user's application cache upon application creation"""
    from authentik.core.api.applications import user_app_cache_key
    from authentik.core.models import Application

    if sender != Application:
        return
    if not created:  # pragma: no cover
        return
    # Also delete user application cache
    keys = cache.keys(user_app_cache_key("*"))
    cache.delete_many(keys)


@receiver(user_logged_in)
# pylint: disable=unused-argument
def user_logged_in_session(sender, request: HttpRequest, user: "User", **_):
    """Create an AuthenticatedSession from request"""
    from authentik.core.models import AuthenticatedSession

    session = AuthenticatedSession.from_request(request, user)
    if session:
        session.save()


@receiver(user_logged_out)
# pylint: disable=unused-argument
def user_logged_out_session(sender, request: HttpRequest, user: "User", **_):
    """Delete AuthenticatedSession if it exists"""
    from authentik.core.models import AuthenticatedSession

    AuthenticatedSession.objects.filter(session_key=request.session.session_key).delete()


@receiver(pre_delete)
def authenticated_session_delete(sender: type[Model], instance: "AuthenticatedSession", **_):
    """Delete session when authenticated session is deleted"""
    from authentik.core.models import AuthenticatedSession

    if sender != AuthenticatedSession:
        return

    cache_key = f"{KEY_PREFIX}{instance.session_key}"
    cache.delete(cache_key)
