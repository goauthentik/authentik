"""authentik outpost signals"""
from django.conf import settings
from django.db.models import Model
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from structlog.stdlib import get_logger

from authentik.core.models import Provider
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.utils.reflection import class_to_path
from authentik.outposts.controllers.base import ControllerException
from authentik.outposts.models import Outpost, OutpostServiceConnection
from authentik.outposts.tasks import outpost_controller_down, outpost_post_save

LOGGER = get_logger()
UPDATE_TRIGGERING_MODELS = (
    Outpost,
    OutpostServiceConnection,
    Provider,
    CertificateKeyPair,
)


@receiver(pre_save, sender=Outpost)
# pylint: disable=unused-argument
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
    dirty += (
        old_instance.config.kubernetes_namespace != instance.config.kubernetes_namespace
    )
    if bool(dirty):
        LOGGER.info("Outpost needs re-deployment due to changes", instance=instance)
        outpost_controller_down_wrapper(old_instance)


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
    outpost_controller_down_wrapper(instance)


def outpost_controller_down_wrapper(instance: Outpost):
    """To ensure that deployment is cleaned up *consistently* we call the controller, and wait
    for it to finish. We don't want to call it in this thread, as we don't have the Outpost
    Service connection here"""
    try:
        outpost_controller_down.delay(instance.pk.hex).get()
    except RuntimeError:  # pragma: no cover
        # In e2e/integration tests, this might run inside a thread/process and
        # trigger the celery `Never call result.get() within a task` detection
        if settings.TEST:
            pass
        else:
            raise
    except ControllerException as exc:
        LOGGER.warning(
            "failed to cleanup outpost deployment", exc=exc, instance=instance
        )
