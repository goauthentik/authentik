"""passbook application administration"""

from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from passbook.admin.mixins import AdminRequiredMixin
from passbook.core.models import Application


class ApplicationListView(AdminRequiredMixin, ListView):
    model = Application
    template_name = 'administration/application/list.html'


class ApplicationCreateView(AdminRequiredMixin, CreateView):

    model = Application
    template_name = 'administration/application/create.html'
    fields = ['name', 'launch_url', 'icon_url']
