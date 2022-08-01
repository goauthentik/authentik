"""proxy provider tasks"""
from django.db import DatabaseError, InternalError, ProgrammingError

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
