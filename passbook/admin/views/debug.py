"""passbook administration debug views"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class DebugRequestView(LoginRequiredMixin, TemplateView):
    """Show debug info about request"""

    template_name = "administration/debug/request.html"

    def get_context_data(self, **kwargs):
        kwargs["request_dict"] = {}
        for key in dir(self.request):
            kwargs["request_dict"][key] = getattr(self.request, key)
        return super().get_context_data(**kwargs)
