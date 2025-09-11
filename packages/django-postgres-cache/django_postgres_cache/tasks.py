from django.utils.timezone import now

from django_postgres_cache.models import CacheEntry


def clear_expired_cache():
    CacheEntry.objects.filter(expires__lt=now()).delete()


try:
    from dramatiq import actor

    @actor
    def clear_expired_cache_task():
        clear_expired_cache()

except ImportError:
    pass
