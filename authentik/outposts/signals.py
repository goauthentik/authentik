"""authentik outpost signals"""

from django.core.cache import cache
from django.db.models import Model
from django.db.models.signals import m2m_changed, post_save, pre_delete, pre_save
from django.dispatch import receiver
from structlog.stdlib import get_logger

from authentik.brands.models import Brand
from authentik.core.models import AuthenticatedSession, Provider
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.utils.reflection import class_to_path
from authentik.outposts.models import Outpost, OutpostServiceConnection
from authentik.outposts.tasks import (
    CACHE_KEY_OUTPOST_DOWN,
    outpost_controller,
    outpost_post_save,
    outpost_session_end,
)

LOGGER = get_logger()
UPDATE_TRIGGERING_MODELS = (
    Outpost,
    OutpostServiceConnection,
    Provider,
    CertificateKeyPair,
    Brand,
)


@receiver(pre_save, sender=Outpost)
def pre_save_outpost(sender, instance: Outpost, **_):
    """Pre-save checks for an outpost, if the name or config.kubernetes_namespace changes,
    we call down and then wait for the up after save"""
    old_instances = Outpost.objects.filter(pk=instance.pk)
    if not old_instances.exists():
        return
    old_instance = old_instances.first()
    dirty = False
    # Name changes the deployment name, need to recreate
    dirty += old_instance.name != instance.name
    # namespace requires re-create
    dirty += old_instance.config.kubernetes_namespace != instance.config.kubernetes_namespace
    if bool(dirty):
        LOGGER.info("Outpost needs re-deployment due to changes", instance=instance)
        cache.set(CACHE_KEY_OUTPOST_DOWN % instance.pk.hex, old_instance)
        outpost_controller.delay(instance.pk.hex, action="down", from_cache=True)


@receiver(m2m_changed, sender=Outpost.providers.through)
def m2m_changed_update(sender, instance: Model, action: str, **_):
    """Update outpost on m2m change, when providers are added or removed"""
    if action in ["post_add", "post_remove", "post_clear"]:
        outpost_post_save.delay(class_to_path(instance.__class__), instance.pk)


@receiver(post_save)
def post_save_update(sender, instance: Model, created: bool, **_):
    """If an Outpost is saved, Ensure that token is created/updated

    If an OutpostModel, or a model that is somehow connected to an OutpostModel is saved,
    we send a message down the relevant OutpostModels WS connection to trigger an update"""
    if instance.__module__ == "django.db.migrations.recorder":
        return
    if instance.__module__ == "__fake__":
        return
    if not isinstance(instance, UPDATE_TRIGGERING_MODELS):
        return
    if isinstance(instance, Outpost) and created:
        LOGGER.info("New outpost saved, ensuring initial token and user are created")
        _ = instance.token
    outpost_post_save.delay(class_to_path(instance.__class__), instance.pk)


@receiver(pre_delete, sender=Outpost)
def pre_delete_cleanup(sender, instance: Outpost, **_):
    """Ensure that Outpost's user is deleted (which will delete the token through cascade)"""
    instance.user.delete()
    cache.set(CACHE_KEY_OUTPOST_DOWN % instance.pk.hex, instance)
    outpost_controller.delay(instance.pk.hex, action="down", from_cache=True)


@receiver(pre_delete, sender=AuthenticatedSession)
def logout_revoke(sender: type[AuthenticatedSession], instance: AuthenticatedSession, **_):
    """Catch logout by expiring sessions being deleted"""
    session_key = instance.session.session_key
    LOGGER.info(
        "Session deletion detected - sending outpost session end",
        session_key=session_key,
        user=instance.user.username,
        session_pk=instance.session.pk,
    )
    outpost_session_end.delay(session_key)
