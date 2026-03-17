from django.utils.timezone import now

from authentik.lib.utils.db import chunked_queryset
from django_postgres_cache.models import CacheEntry


def clear_expired_cache() -> None:
    # FIXME: this is currently imported from the main project,
    # do we copy it here to make it independent?
    for obj in chunked_queryset(CacheEntry.objects.filter(expires__lt=now())):
        obj.delete()
