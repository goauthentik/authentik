from authentik.events.models import Event, EventAction
from authentik.stages.authenticator.models import Device


def device_post_save_event(sender, instance: Device, created: bool, raw: bool, **_):
    """Log an event when an MFA device is added."""
    if raw or not instance.confirmed:
        return
    was_confirmed = getattr(instance, "_loaded_confirmed", False)
    instance._loaded_confirmed = instance.confirmed
    if not created and was_confirmed:
        return

    Event.new(
        EventAction.MFA_DEVICE_ADDED,
        affected_user_pk=instance.user.pk,
        mfa_device={"type": instance._meta.model_name, "name": instance.name, "pk": instance.pk},
    ).from_ctx_request()


def device_pre_delete_event(sender, instance: Device, origin, **_):
    """Log an event when an MFA device is removed."""
    if not instance.confirmed:
        return
    if instance != origin:
        return
    Event.new(
        EventAction.MFA_DEVICE_REMOVED,
        affected_user_pk=instance.user.pk,
        mfa_device={"type": instance._meta.model_name, "name": instance.name, "pk": instance.pk},
    ).from_ctx_request()
