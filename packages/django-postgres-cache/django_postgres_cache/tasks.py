from django.utils.timezone import now

from authentik.lib.utils.db import delete_in_batches
from django_postgres_cache.models import CacheEntry


def clear_expired_cache() -> int:
    """Delete unlocked expired entries and return the number removed."""
    # FIXME: this is currently imported from the main project,
    # do we copy it here to make it independent?
    return delete_in_batches(CacheEntry.objects.filter(expires__lt=now()))
