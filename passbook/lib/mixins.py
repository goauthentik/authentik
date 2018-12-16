"""passbook util mixins"""
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


class CSRFExemptMixin:
    """wrapper to apply @csrf_exempt to CBV"""

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        """wrapper to apply @csrf_exempt to CBV"""
        return super().dispatch(*args, **kwargs)
