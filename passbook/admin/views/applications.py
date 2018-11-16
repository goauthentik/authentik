"""passbook application administration"""

from django.views.generic import CreateView, ListView

from passbook.admin.mixins import AdminRequiredMixin
from passbook.core.models import Application


class ApplicationListView(AdminRequiredMixin, ListView):
    """List all applications"""

    model = Application
    template_name = 'administration/application/list.html'


class ApplicationCreateView(AdminRequiredMixin, CreateView):
    """Create new application"""

    model = Application
    template_name = 'administration/application/create.html'
    fields = ['name', 'launch_url', 'icon_url']
