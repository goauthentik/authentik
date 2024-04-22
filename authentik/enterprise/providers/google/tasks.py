from authentik.enterprise.providers.google.clients.users import GoogleUserSync
from authentik.enterprise.providers.google.models import GoogleProvider
from authentik.root.celery import CELERY_APP


@CELERY_APP.task()
def google_sync(provider_pk):
    provider = GoogleProvider.objects.filter(pk=provider_pk).first()
    if not provider:
        return

    GoogleUserSync(provider).run()
