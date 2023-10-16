"""proxy provider tasks"""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import DatabaseError, InternalError, ProgrammingError

from authentik.outposts.consumer import OUTPOST_GROUP
from authentik.outposts.models import Outpost, OutpostType
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
        group = OUTPOST_GROUP % {"outpost_pk": str(outpost.pk)}
        async_to_sync(layer.group_send)(
            group,
            {
                "type": "event.provider.specific",
                "sub_type": "logout",
                "session_id": session_id,
            },
        )
