"""RAC Signals"""

from channels.layers import get_channel_layer
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver

from authentik.core.models import AuthenticatedSession
from authentik.endpoints.models import Device, DeviceUserBinding
from authentik.providers.rac.api.devices import user_device_cache_key
from authentik.providers.rac.consumer_client import (
    build_rac_client_group_session,
    build_rac_client_group_token,
)
from authentik.providers.rac.models import ConnectionToken


@receiver(pre_delete, sender=AuthenticatedSession)
def user_session_deleted(sender, instance: AuthenticatedSession, **_):
    layer = get_channel_layer()
    layer.group_send_blocking(
        build_rac_client_group_session(instance.session.session_key),
        {"type": "event.disconnect", "reason": "session_logout"},
    )


@receiver(pre_delete, sender=ConnectionToken)
def pre_delete_connection_token_disconnect(sender, instance: ConnectionToken, **_):
    """Disconnect session when connection token is deleted"""
    layer = get_channel_layer()
    layer.group_send_blocking(
        build_rac_client_group_token(instance.token),
        {"type": "event.disconnect", "reason": "token_delete"},
    )


@receiver([post_save, post_delete], sender=Device)
@receiver([post_save, post_delete], sender=DeviceUserBinding)
def post_save_post_delete_device(**_):
    """Clear the cached device list when devices or their bindings change"""
    keys = cache.keys(user_device_cache_key("*", "*"))
    cache.delete_many(keys)
