"""passbook Application administration"""
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from passbook.admin.mixins import AdminRequiredMixin
from passbook.core.forms.applications import ApplicationForm
from passbook.core.models import Application


class ApplicationListView(AdminRequiredMixin, ListView):
    """Show list of all applications"""

    model = Application
    template_name = 'administration/application/list.html'

    def get_queryset(self):
        return super().get_queryset().select_subclasses()


class ApplicationCreateView(SuccessMessageMixin, AdminRequiredMixin, CreateView):
    """Create new Application"""

    form_class = ApplicationForm

    template_name = 'generic/create.html'
    success_url = reverse_lazy('passbook_admin:applications')
    success_message = _('Successfully created Application')


class ApplicationUpdateView(SuccessMessageMixin, AdminRequiredMixin, UpdateView):
    """Update application"""

    model = Application
    form_class = ApplicationForm

    template_name = 'generic/update.html'
    success_url = reverse_lazy('passbook_admin:applications')
    success_message = _('Successfully updated Application')


class ApplicationDeleteView(SuccessMessageMixin, AdminRequiredMixin, DeleteView):
    """Delete application"""

    model = Application

    template_name = 'generic/delete.html'
    success_url = reverse_lazy('passbook_admin:applications')
    success_message = _('Successfully deleted Application')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)
