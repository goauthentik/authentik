"""passbook outpost signals"""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Model
from django.db.models.signals import post_save
from django.dispatch import receiver
from structlog import get_logger

from passbook.outposts.models import Outpost, OutpostModel

LOGGER = get_logger()


@receiver(post_save, sender=Outpost)
# pylint: disable=unused-argument
def ensure_user_and_token(sender, instance, **_):
    """Ensure that token is created/updated on save"""
    _ = instance.token


@receiver(post_save)
# pylint: disable=unused-argument
def post_save_update(sender, instance, **_):
    """If an OutpostModel, or a model that is somehow connected to an OutpostModel is saved,
    we send a message down the relevant OutpostModels WS connection to trigger an update"""
    if isinstance(instance, OutpostModel):
        LOGGER.debug("triggering outpost update from outpostmodel", instance=instance)
        _send_update(instance)
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
            _send_update(reverse)


def _send_update(outpost_model: Model):
    """Send update trigger for each channel of an outpost model"""
    for outpost in outpost_model.outpost_set.all():
        channel_layer = get_channel_layer()
        for channel in outpost.channels:
            print(f"sending update to channel {channel}")
            async_to_sync(channel_layer.send)(channel, {"type": "event.update"})
