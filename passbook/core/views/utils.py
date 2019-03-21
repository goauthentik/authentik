"""passbook core utils view"""
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView


class LoadingView(TemplateView):
    """View showing a loading template, and forwarding to real view using html forwarding."""

    template_name = 'login/loading.html'
    title = _('Loading')
    target_url = None

    def get_url(self):
        """Return URL template will redirect to"""
        return self.target_url

    def get_context_data(self, **kwargs):
        kwargs['is_login'] = True
        kwargs['title'] = self.title
        kwargs['target_url'] = self.get_url()
        return super().get_context_data(**kwargs)

class PermissionDeniedView(TemplateView):
    """Generic Permission denied view"""

    template_name = 'login/denied.html'
    title = _('Permission denied.')

    def get_context_data(self, **kwargs):
        kwargs['is_login'] = True
        kwargs['title'] = self.title
        return super().get_context_data(**kwargs)
