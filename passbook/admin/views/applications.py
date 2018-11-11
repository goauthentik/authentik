"""passbook application administration"""

from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from passbook.core.models import Application


class ApplicationListView(ListView):
    model = Application
    template_name = 'administration/list.html'

class ApplicationCreateView(CreateView):

    model = Application
    template_name = 'administration/application/create.html'
    fields = ['name', 'launch_url', 'icon_url']
