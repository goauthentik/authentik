"""authentik outpost signals"""

from django.core.cache import cache
from django.db.models.signals import m2m_changed, post_save, pre_delete, pre_save
from django.dispatch import receiver
from structlog.stdlib import get_logger

from authentik.brands.models import Brand
from authentik.core.models import AuthenticatedSession, Provider
from authentik.crypto.models import CertificateKeyPair
from authentik.outposts.models import Outpost, OutpostModel, OutpostServiceConnection
from authentik.outposts.tasks import (
    CACHE_KEY_OUTPOST_DOWN,
    outpost_controller,
    outpost_send_update,
    outpost_session_end,
)

LOGGER = get_logger()


@receiver(pre_save, sender=Outpost)
def outpost_pre_save(sender, instance: Outpost, **_):
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
        outpost_controller.send_with_options(
            args=(instance.pk.hex,),
            kwargs={"action": "down", "from_cache": True},
            rel_obj=instance,
        )


@receiver(m2m_changed, sender=Outpost.providers.through)
def outpost_m2m_changed(sender, instance: Outpost | Provider, action: str, **_):
    """Update outpost on m2m change, when providers are added or removed"""
    if action not in ["post_add", "post_remove", "post_clear"]:
        return
    if isinstance(instance, Outpost):
        outpost_controller.send_with_options(
            args=(instance.pk,),
            rel_obj=instance.service_connection,
        )
        outpost_send_update.send_with_options(args=(instance.pk,), rel_obj=instance)
    elif isinstance(instance, OutpostModel):
        for outpost in instance.outpost_set.all():
            outpost_controller.send_with_options(
                args=(instance.pk,),
                rel_obj=instance.service_connection,
            )
            outpost_send_update.send_with_options(args=(outpost.pk,), rel_obj=outpost)


@receiver(post_save, sender=Outpost)
def outpost_post_save(sender, instance: Outpost, created: bool, **_):
    if created:
        LOGGER.info("New outpost saved, ensuring initial token and user are created")
        _ = instance.token
    outpost_controller.send_with_options(args=(instance.pk,), rel_obj=instance.service_connection)
    outpost_send_update.send_with_options(args=(instance.pk,), rel_obj=instance)


def outpost_related_post_save(sender, instance: OutpostServiceConnection | OutpostModel, **_):
    for outpost in instance.outpost_set.all():
        outpost_send_update.send_with_options(args=(outpost.pk,), rel_obj=outpost)


post_save.connect(outpost_related_post_save, sender=OutpostServiceConnection, weak=False)
for subclass in OutpostModel.__subclasses__():
    post_save.connect(outpost_related_post_save, sender=subclass, weak=False)


def outpost_reverse_related_post_save(sender, instance: CertificateKeyPair | Brand, **_):
    for field in instance._meta.get_fields():
        # Each field is checked if it has a `related_model` attribute (when ForeginKeys or M2Ms)
        # are used, and if it has a value
        if not hasattr(field, "related_model"):
            continue
        if not field.related_model:
            continue
        if not issubclass(field.related_model, OutpostModel):
            continue

        field_name = f"{field.name}_set"
        if not hasattr(instance, field_name):
            continue

        LOGGER.debug("triggering outpost update from field", field=field.name)
        # Because the Outpost Model has an M2M to Provider,
        # we have to iterate over the entire QS
        for reverse in getattr(instance, field_name).all():
            if isinstance(reverse, OutpostModel):
                for outpost in reverse.outpost_set.all():
                    outpost_send_update.send_with_options(args=(outpost.pk,), rel_obj=outpost)


post_save.connect(outpost_reverse_related_post_save, sender=Brand, weak=False)
post_save.connect(outpost_reverse_related_post_save, sender=CertificateKeyPair, weak=False)


@receiver(pre_delete, sender=Outpost)
def outpost_pre_delete_cleanup(sender, instance: Outpost, **_):
    """Ensure that Outpost's user is deleted (which will delete the token through cascade)"""
    instance.user.delete()
    cache.set(CACHE_KEY_OUTPOST_DOWN % instance.pk.hex, instance)
    outpost_controller.send(instance.pk.hex, action="down", from_cache=True)


@receiver(pre_delete, sender=AuthenticatedSession)
def outpost_logout_revoke(sender: type[AuthenticatedSession], instance: AuthenticatedSession, **_):
    """Catch logout by expiring sessions being deleted"""
    outpost_session_end.send(instance.session.session_key)
