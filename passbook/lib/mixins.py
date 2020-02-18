"""passbook util mixins"""
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


class CSRFExemptMixin:
    """wrapper to apply @csrf_exempt to CBV"""

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        """wrapper to apply @csrf_exempt to CBV"""
        return super().dispatch(*args, **kwargs)


class NeverCacheMixin:
    """Use never_cache as mixin for CBV"""

    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        """Use never_cache as mixin for CBV"""
        return super().dispatch(*args, **kwargs)
