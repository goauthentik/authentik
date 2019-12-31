"""passbook django boilerplate code"""
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache


class NeverCacheMixin:
    """Use never_cache as mixin for CBV"""

    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        """Use never_cache as mixin for CBV"""
        return super().dispatch(*args, **kwargs)
