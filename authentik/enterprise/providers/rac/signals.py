"""RAC Signals"""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.http import HttpRequest

from authentik.core.models import User
from authentik.enterprise.providers.rac.consumer_client import RAC_CLIENT_GROUP_SESSION


@receiver(user_logged_out)
def user_logged_out_session(sender, request: HttpRequest, user: User, **_):
    """Disconnect any open RAC connections"""
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(
        RAC_CLIENT_GROUP_SESSION
        % {
            "session": request.session.session_key,
        },
        {"type": "event.disconnect", "reason": "logout"},
    )
