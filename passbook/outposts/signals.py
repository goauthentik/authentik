"""passbook outpost signals"""
from django.db.models import Model
from django.db.models.signals import post_save
from django.dispatch import receiver
from structlog import get_logger

from passbook.lib.utils.reflection import class_to_path
from passbook.outposts.models import Outpost, OutpostModel
from passbook.outposts.tasks import outpost_send_update

LOGGER = get_logger()


@receiver(post_save, sender=Outpost)
# pylint: disable=unused-argument
def ensure_user_and_token(sender, instance: Model, **_):
    """Ensure that token is created/updated on save"""
    _ = instance.token


@receiver(post_save)
# pylint: disable=unused-argument
def post_save_update(sender, instance: Model, **_):
    """If an OutpostModel, or a model that is somehow connected to an OutpostModel is saved,
    we send a message down the relevant OutpostModels WS connection to trigger an update"""
    if isinstance(instance, OutpostModel):
        LOGGER.debug("triggering outpost update from outpostmodel", instance=instance)
        outpost_send_update.delay(class_to_path(instance.__class__), instance.pk)
        return

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

        LOGGER.debug("triggering outpost update from from field", field=field.name)
        # Because the Outpost Model has an M2M to Provider,
        # we have to iterate over the entire QS
        for reverse in getattr(instance, field_name).all():
            outpost_send_update(class_to_path(reverse.__class__), reverse.pk)
