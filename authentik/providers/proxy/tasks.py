"""proxy provider tasks"""
from authentik.providers.proxy.models import ProxyProvider
from authentik.root.celery import CELERY_APP


@CELERY_APP.task()
def proxy_set_defaults():
    """Ensure correct defaults are set for all providers"""
    for provider in ProxyProvider.objects.all():
        provider.set_oauth_defaults()
        provider.save()
