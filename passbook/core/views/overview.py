"""passbook overview views"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class OverviewView(LoginRequiredMixin, TemplateView):
    """Overview for logged in user, incase user opens passbook directly
    and is not being forwarded"""

    template_name = 'overview/index.html'
