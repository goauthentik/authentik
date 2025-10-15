# django-postgres-cache

### Use in migrations

Migrations that use the cache with this installed need to depend on the migration to create the cache entry table:

```python
    dependencies = [
        # ...other requirements
        ("django_postgres_cache", "0001_initial"),
    ]
```
