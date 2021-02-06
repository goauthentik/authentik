"""authentik administration overview"""
from django.contrib.messages.views import SuccessMessageMixin
from django.core.cache import cache
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.urls.base import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import FormView
from structlog.stdlib import get_logger

from authentik.admin.forms.overview import FlowCacheClearForm, PolicyCacheClearForm
from authentik.admin.mixins import AdminRequiredMixin
from authentik.core.api.applications import user_app_cache_key

LOGGER = get_logger()


class PolicyCacheClearView(AdminRequiredMixin, SuccessMessageMixin, FormView):
    """View to clear Policy cache"""

    form_class = PolicyCacheClearForm

    template_name = "generic/form_non_model.html"
    success_url = reverse_lazy("authentik_core:shell")
    success_message = _("Successfully cleared Policy cache")

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        keys = cache.keys("policy_*")
        cache.delete_many(keys)
        LOGGER.debug("Cleared Policy cache", keys=len(keys))
        # Also delete user application cache
        keys = cache.keys(user_app_cache_key("*"))
        cache.delete_many(keys)
        return super().post(request, *args, **kwargs)


class FlowCacheClearView(AdminRequiredMixin, SuccessMessageMixin, FormView):
    """View to clear Flow cache"""

    form_class = FlowCacheClearForm

    template_name = "generic/form_non_model.html"
    success_url = reverse_lazy("authentik_core:shell")
    success_message = _("Successfully cleared Flow cache")

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        keys = cache.keys("flow_*")
        cache.delete_many(keys)
        LOGGER.debug("Cleared flow cache", keys=len(keys))
        return super().post(request, *args, **kwargs)
