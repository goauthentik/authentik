from django.db import models


class CacheEntry(models.Model):

    cache_key = models.TextField(unique=True, primary_key=True)
    value = models.TextField()
    expires = models.DateTimeField(db_index=True)

    class Meta:
        default_permissions = []
        db_table = ""

    def __str__(self) -> str:
        return f"Cache entry '{self.cache_key}'"
