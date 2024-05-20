"""RAC Signals"""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.signals import user_logged_out
from django.core.cache import cache
from django.db.models import Model
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.http import HttpRequest

from authentik.core.models import User
from authentik.enterprise.providers.rac.api.endpoints import user_endpoint_cache_key
from authentik.enterprise.providers.rac.consumer_client import (
    RAC_CLIENT_GROUP_SESSION,
    RAC_CLIENT_GROUP_TOKEN,
)
from authentik.enterprise.providers.rac.models import ConnectionToken, Endpoint


@receiver(user_logged_out)
def user_logged_out_session(sender, request: HttpRequest, user: User, **_):
    """Disconnect any open RAC connections"""
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(
        RAC_CLIENT_GROUP_SESSION
        % {
            "session": request.session.session_key,
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


@receiver(post_save, sender=Endpoint)
def post_save_endpoint(sender: type[Model], instance, created: bool, **_):
    """Clear user's endpoint cache upon endpoint creation"""
    if not created:  # pragma: no cover
        return

    # Delete user endpoint cache
    keys = cache.keys(user_endpoint_cache_key("*"))
    cache.delete_many(keys)
