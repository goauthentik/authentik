"""authentik core app config"""
from importlib import import_module

from django.apps import AppConfig

from authentik.core.signals import GAUGE_MODELS
from authentik.lib.utils.reflection import get_apps


class AuthentikCoreConfig(AppConfig):
    """authentik core app config"""

    name = "authentik.core"
    label = "authentik_core"
    verbose_name = "authentik Core"
    mountpoint = ""

    def ready(self):
        import_module("authentik.core.signals")
        import_module("authentik.core.managed")
        for app in get_apps():
            for model in app.get_models():
                GAUGE_MODELS.labels(
                    model_name=model._meta.model_name,
                    app=model._meta.app_label,
                ).set(model.objects.count())
