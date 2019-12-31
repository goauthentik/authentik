"""passbook Application administration"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import DeleteView, ListView, UpdateView
from guardian.mixins import PermissionListMixin, PermissionRequiredMixin

from passbook.core.forms.applications import ApplicationForm
from passbook.core.models import Application
from passbook.lib.views import CreateAssignPermView


class ApplicationListView(LoginRequiredMixin, PermissionListMixin, ListView):
    """Show list of all applications"""

    model = Application
    permission_required = "passbook_core.view_application"
    ordering = "name"
    paginate_by = 40
    template_name = "administration/application/list.html"

    def get_queryset(self):
        return super().get_queryset().select_subclasses()


class ApplicationCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new Application"""

    model = Application
    form_class = ApplicationForm
    permission_required = "passbook_core.add_application"

    template_name = "generic/create.html"
    success_url = reverse_lazy("passbook_admin:applications")
    success_message = _("Successfully created Application")

    def get_context_data(self, **kwargs):
        kwargs["type"] = "Application"
        return super().get_context_data(**kwargs)


class ApplicationUpdateView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """Update application"""

    model = Application
    form_class = ApplicationForm
    permission_required = "passbook_core.change_application"

    template_name = "generic/update.html"
    success_url = reverse_lazy("passbook_admin:applications")
    success_message = _("Successfully updated Application")


class ApplicationDeleteView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    """Delete application"""

    model = Application
    permission_required = "passbook_core.delete_application"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("passbook_admin:applications")
    success_message = _("Successfully deleted Application")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)
