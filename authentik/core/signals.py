"""authentik core signals"""

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


@receiver(post_save, sender=Application)
def post_save_application_saml_issuer(sender: type[Model], instance: Application, **_):
    """Generate SAML provider issuer when application is linked to a SAML provider"""
    from authentik.lib.config import CONFIG
    from authentik.providers.saml.models import SAMLProvider

    LOGGER.debug("Application saved, checking for SAML issuer generation", app=instance.slug)

    # Only process if application has a provider
    if not instance.provider:
        LOGGER.debug("Application has no provider, skipping", app=instance.slug)
        return

    # Check if provider is a SAML provider by trying to access the samlprovider attribute
    try:
        provider = instance.provider.samlprovider
    except (AttributeError, SAMLProvider.DoesNotExist):
        LOGGER.debug(
            "Provider is not SAML, skipping",
            app=instance.slug,
            provider_type=type(instance.provider).__name__,
        )
        return

    # Only set issuer if it's null
    if provider.issuer:
        LOGGER.debug(
            "Issuer already set, skipping",
            app=instance.slug,
            provider=provider.name,
            issuer=provider.issuer,
        )
        return

    # Generate the issuer URL
    scheme = "https" if not CONFIG.get_bool("authentik.debug", False) else "http"
    domain = CONFIG.get("server.domain", "localhost:9000")
    path = f"/application/saml/{instance.slug}/"
    provider.issuer = f"{scheme}://{domain}{path}"
    provider.save()

    LOGGER.info(
        "Generated issuer for SAML provider",
        provider=provider.name,
        application=instance.slug,
        issuer=provider.issuer,
    )


@receiver(user_logged_in)
def user_logged_in_session(sender, request: HttpRequest, user: User, **_):
    """Create an AuthenticatedSession from request"""

    session = AuthenticatedSession.from_request(request, user)
    if session:
        session.save()


@receiver(post_delete, sender=AuthenticatedSession)
def authenticated_session_delete(sender: type[Model], instance: "AuthenticatedSession", **_):
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
