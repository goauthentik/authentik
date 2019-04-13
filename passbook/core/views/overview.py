"""passbook overview views"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from guardian.shortcuts import get_objects_for_user


class OverviewView(LoginRequiredMixin, TemplateView):
    """Overview for logged in user, incase user opens passbook directly
    and is not being forwarded"""

    template_name = 'overview/index.html'

    def get_context_data(self, **kwargs):
        kwargs['applications'] = get_objects_for_user(self.request.user,
                                                      'passbook_core.view_application')
        return super().get_context_data(**kwargs)
