from django.utils.timezone import now

from django_postgres_cache.models import CacheEntry


def clear_expired_cache() -> None:
    # TODO: optimize deletion, possibly chunking it like we do elsewhere
    CacheEntry.objects.filter(expires__lt=now()).delete()


try:
    from dramatiq import actor

    @actor(description="Clean up expired cache keys")
    def clear_expired_cache_task() -> None:
        clear_expired_cache()

except ImportError:
    pass
