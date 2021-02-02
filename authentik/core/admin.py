"""authentik core admin"""

from django.apps import AppConfig, apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from guardian.admin import GuardedModelAdmin


def admin_autoregister(app: AppConfig):
    """Automatically register all models from app"""
    for model in app.get_models():
        try:
            admin.site.register(model, GuardedModelAdmin)
        except AlreadyRegistered:
            pass


for _app in apps.get_app_configs():
    if _app.label.startswith("authentik_"):
        admin_autoregister(_app)
