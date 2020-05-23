"""passbook core utils view"""
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView


class PermissionDeniedView(TemplateView):
    """Generic Permission denied view"""

    template_name = "login/denied.html"
    title = _("Permission denied.")

    def get_context_data(self, **kwargs):
        kwargs["title"] = self.title
        return super().get_context_data(**kwargs)
