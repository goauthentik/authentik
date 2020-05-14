"""passbook Flow administration"""
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

from passbook.flows.forms import FlowForm
from passbook.flows.models import Flow
from passbook.lib.views import CreateAssignPermView


class FlowListView(LoginRequiredMixin, PermissionListMixin, ListView):
    """Show list of all flows"""

    model = Flow
    permission_required = "passbook_flows.view_flow"
    ordering = "name"
    paginate_by = 40
    template_name = "administration/flow/list.html"


class FlowCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new Flow"""

    model = Flow
    form_class = FlowForm
    permission_required = "passbook_flows.add_flow"

    template_name = "generic/create.html"
    success_url = reverse_lazy("passbook_admin:flows")
    success_message = _("Successfully created Flow")

    def get_context_data(self, **kwargs):
        kwargs["type"] = "Flow"
        return super().get_context_data(**kwargs)


class FlowUpdateView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """Update flow"""

    model = Flow
    form_class = FlowForm
    permission_required = "passbook_flows.change_flow"

    template_name = "generic/update.html"
    success_url = reverse_lazy("passbook_admin:flows")
    success_message = _("Successfully updated Flow")


class FlowDeleteView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    """Delete flow"""

    model = Flow
    permission_required = "passbook_flows.delete_flow"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("passbook_admin:flows")
    success_message = _("Successfully deleted Flow")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)
