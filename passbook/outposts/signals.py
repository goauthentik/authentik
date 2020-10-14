"""passbook outpost signals"""
from django.db.models import Model
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from structlog import get_logger

from passbook.lib.utils.reflection import class_to_path
from passbook.outposts.models import Outpost
from passbook.outposts.tasks import outpost_post_save

LOGGER = get_logger()


@receiver(post_save)
# pylint: disable=unused-argument
def post_save_update(sender, instance: Model, **_):
    """If an Outpost is saved, Ensure that token is created/updated

    If an OutpostModel, or a model that is somehow connected to an OutpostModel is saved,
    we send a message down the relevant OutpostModels WS connection to trigger an update"""
    outpost_post_save.delay(class_to_path(instance.__class__), instance.pk)


@receiver(pre_delete, sender=Outpost)
# pylint: disable=unused-argument
def pre_delete_cleanup(sender, instance: Outpost, **_):
    """Ensure that Outpost's user is deleted (which will delete the token through cascade)"""
    instance.user.delete()
