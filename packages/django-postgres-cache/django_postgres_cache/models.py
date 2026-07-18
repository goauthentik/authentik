from django.db import models
from psqlextra.manager import PostgresManager


class CacheEntry(models.Model):
    cache_key = models.TextField(primary_key=True)
    value = models.TextField()
    expires = models.DateTimeField(db_index=True)

    objects = PostgresManager()  # type: ignore[no-untyped-call]

    class Meta:
        default_permissions = []

    def __str__(self) -> str:
        return f"Cache entry '{self.cache_key}'"
