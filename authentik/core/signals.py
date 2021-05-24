"""authentik core signals"""
from django.core.cache import cache
from django.core.signals import Signal
from django.db.models import Model
from django.db.models.signals import post_save
from django.dispatch import receiver
from prometheus_client import Gauge

# Arguments: user: User, password: str
password_changed = Signal()

GAUGE_MODELS = Gauge(
    "authentik_models", "Count of various objects", ["model_name", "app"]
)


@receiver(post_save)
# pylint: disable=unused-argument
def post_save_application(sender: type[Model], instance, created: bool, **_):
    """Clear user's application cache upon application creation"""
    from authentik.core.api.applications import user_app_cache_key
    from authentik.core.models import Application

    GAUGE_MODELS.labels(
        model_name=sender._meta.model_name,
        app=sender._meta.app_label,
    ).set(sender.objects.count())

    if sender != Application:
        return
    if not created:  # pragma: no cover
        return
    # Also delete user application cache
    keys = cache.keys(user_app_cache_key("*"))
    cache.delete_many(keys)
