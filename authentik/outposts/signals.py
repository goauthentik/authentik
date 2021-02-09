"""authentik outpost signals"""
from django.db.models import Model
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from structlog.stdlib import get_logger

from authentik.core.models import Provider
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.utils.reflection import class_to_path
from authentik.outposts.models import Outpost, OutpostServiceConnection
from authentik.outposts.tasks import outpost_post_save, outpost_pre_delete

LOGGER = get_logger()
UPDATE_TRIGGERING_MODELS = (
    Outpost,
    OutpostServiceConnection,
    Provider,
    CertificateKeyPair,
)


@receiver(post_save)
# pylint: disable=unused-argument
def post_save_update(sender, instance: Model, **_):
    """If an Outpost is saved, Ensure that token is created/updated

    If an OutpostModel, or a model that is somehow connected to an OutpostModel is saved,
    we send a message down the relevant OutpostModels WS connection to trigger an update"""
    if instance.__module__ == "django.db.migrations.recorder":
        return
    if instance.__module__ == "__fake__":
        return
    if not isinstance(instance, UPDATE_TRIGGERING_MODELS):
        return
    outpost_post_save.delay(class_to_path(instance.__class__), instance.pk)


@receiver(pre_delete, sender=Outpost)
# pylint: disable=unused-argument
def pre_delete_cleanup(sender, instance: Outpost, **_):
    """Ensure that Outpost's user is deleted (which will delete the token through cascade)"""
    instance.user.delete()
    # To ensure that deployment is cleaned up *consistently* we call the controller, and wait
    # for it to finish. We don't want to call it in this thread, as we don't have the K8s
    # credentials here
    outpost_pre_delete.delay(instance.pk.hex).get()
