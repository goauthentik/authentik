"""passbook overview views"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class OverviewView(LoginRequiredMixin, TemplateView):
    """Overview for logged in user, incase user opens passbook directly
    and is not being forwarded"""

    template_name = 'overview/index.html'

    def get_context_data(self, **kwargs):
        kwargs['applications'] = self.request.user.applications.objects.all()
        return super().get_context_data(**kwargs)
