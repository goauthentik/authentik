"""totp authenticator signals"""
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from authentik.events.models import Event
from authentik.stages.authenticator_static.models import StaticDevice


@receiver(pre_delete, sender=StaticDevice)
def pre_delete_event(sender, instance: StaticDevice, **_):
    """Create event before deleting Static Devices"""
    # Create event with email notification
    event = Event.new("static_authenticator_disable", message="User disabled Static OTP Tokens.")
    event.set_user(instance.user)
    event.save()
