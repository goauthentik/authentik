"""totp authenticator signals"""
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django_otp.plugins.otp_totp.models import TOTPDevice

from authentik.events.models import Event


@receiver(pre_delete, sender=TOTPDevice)
# pylint: disable=unused-argument
def pre_delete_event(sender, instance: TOTPDevice, **_):
    # Create event with email notification
    event = Event.new("totp_disable", message="User disabled Time-based OTP.")
    event.set_user(instance.user)
    event.save()
