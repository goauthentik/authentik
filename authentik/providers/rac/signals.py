"""RAC Signals"""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver

from authentik.core.models import AuthenticatedSession
from authentik.providers.rac.api.endpoints import user_endpoint_cache_key
from authentik.providers.rac.consumer_client import (
    RAC_CLIENT_GROUP_SESSION,
    RAC_CLIENT_GROUP_TOKEN,
)
from authentik.providers.rac.models import ConnectionToken, Endpoint


@receiver(pre_delete, sender=AuthenticatedSession)
def user_session_deleted(sender, instance: AuthenticatedSession, **_):
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(
        RAC_CLIENT_GROUP_SESSION
        % {
            "session": instance.session.session_key,
        },
        {"type": "event.disconnect", "reason": "session_logout"},
    )


@receiver(pre_delete, sender=ConnectionToken)
def pre_delete_connection_token_disconnect(sender, instance: ConnectionToken, **_):
    """Disconnect session when connection token is deleted"""
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(
        RAC_CLIENT_GROUP_TOKEN
        % {
            "token": instance.token,
        },
        {"type": "event.disconnect", "reason": "token_delete"},
    )


@receiver([post_save, post_delete], sender=Endpoint)
def post_save_post_delete_endpoint(**_):
    """Clear user's endpoint cache upon endpoint creation or deletion"""
    keys = cache.keys(user_endpoint_cache_key("*", "*"))
    cache.delete_many(keys)
