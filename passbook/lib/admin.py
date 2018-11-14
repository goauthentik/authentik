"""passbook core admin"""

from django.apps import apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from django.contrib.auth.admin import UserAdmin

from passbook.core.models import User


def admin_autoregister(app):
    """Automatically register all models from app"""
    app_models = apps.get_app_config(app).get_models()
    for model in app_models:
        try:
            admin.site.register(model)
        except AlreadyRegistered:
            pass


admin.site.register(User, UserAdmin)
admin_autoregister('passbook_core')
