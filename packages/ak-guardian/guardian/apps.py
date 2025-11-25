from django.apps import AppConfig
from django.db.models.signals import post_migrate


class GuardianConfig(AppConfig):
    name = "guardian"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from .shortcuts import clear_ct_cache

        post_migrate.connect(clear_ct_cache)
