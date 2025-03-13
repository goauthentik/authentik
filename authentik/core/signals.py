"""authentik core signals"""

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.core.cache import cache
from django.core.signals import Signal
from django.db.models import Model
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.http.request import HttpRequest
from structlog.stdlib import get_logger

from authentik.core.models import (
    Application,
    AuthenticatedSession,
    BackchannelProvider,
    ExpiringModel,
    Session,
    User,
    default_token_duration,
)

# Arguments: user: User, password: str
password_changed = Signal()
# Arguments: credentials: dict[str, any], request: HttpRequest, stage: Stage
login_failed = Signal()

LOGGER = get_logger()


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

    session = AuthenticatedSession.from_request(request, user)
    if session:
        session.save()


@receiver(user_logged_out)
def user_logged_out_session(sender, request: HttpRequest, user: User, **_):
    """Delete AuthenticatedSession if it exists"""
    if not request.session or not request.session.session_key:
        return
    AuthenticatedSession.objects.filter(session__session_key=request.session.session_key).delete()


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


@receiver(post_delete)
def authenticated_session_post_delete(sender: type[Model], instance: AuthenticatedSession, **_):
    """Ensure Session objects associated with an AuthenticatedSession are also deleted"""
    Session.objects.filter(pk=instance.pk).delete()
