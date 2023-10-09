"""proxy provider tasks"""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import DatabaseError, InternalError, ProgrammingError

from authentik.outposts.models import Outpost, OutpostState, OutpostType
from authentik.providers.proxy.models import ProxyProvider
from authentik.root.celery import CELERY_APP


@CELERY_APP.task(
    throws=(DatabaseError, ProgrammingError, InternalError),
)
def proxy_set_defaults():
    """Ensure correct defaults are set for all providers"""
    for provider in ProxyProvider.objects.all():
        provider.set_oauth_defaults()
        provider.save()


@CELERY_APP.task()
def proxy_on_logout(session_id: str):
    """Update outpost instances connected to a single outpost"""
    layer = get_channel_layer()
    for outpost in Outpost.objects.filter(type=OutpostType.PROXY):
        for state in OutpostState.for_outpost(outpost):
            for channel in state.channel_ids:
                async_to_sync(layer.send)(
                    channel,
                    {
                        "type": "event.provider.specific",
                        "sub_type": "logout",
                        "session_id": session_id,
                    },
                )
