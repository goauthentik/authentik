"""passbook core admin"""

from django.apps import AppConfig, apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from guardian.admin import GuardedModelAdmin
from structlog import get_logger

LOGGER = get_logger()


def admin_autoregister(app: AppConfig):
    """Automatically register all models from app"""
    for model in app.get_models():
        try:
            admin.site.register(model, GuardedModelAdmin)
        except AlreadyRegistered:
            pass


for _app in apps.get_app_configs():
    if _app.label.startswith("passbook_"):
        LOGGER.debug("Registering application for dj-admin", app=_app.label)
        admin_autoregister(_app)
