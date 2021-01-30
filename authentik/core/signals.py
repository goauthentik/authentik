"""authentik core signals"""
from django.core.cache import cache
from django.core.signals import Signal
from django.db.models.signals import post_save
from django.dispatch import receiver

# Arguments: user: User, password: str
password_changed = Signal()


@receiver(post_save)
# pylint: disable=unused-argument
def post_save_application(sender, instance, created: bool, **_):
    """Clear user's application cache upon application creation"""
    from authentik.core.models import Application
    from authentik.core.api.applications import user_app_cache_key

    if sender != Application:
        return
    if not created:
        return
    # Also delete user application cache
    keys = cache.keys(user_app_cache_key("*"))
    cache.delete_many(keys)
