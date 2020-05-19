"""passbook StageBinding administration"""
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

from passbook.flows.forms import FlowStageBindingForm
from passbook.flows.models import FlowStageBinding
from passbook.lib.views import CreateAssignPermView


class StageBindingListView(LoginRequiredMixin, PermissionListMixin, ListView):
    """Show list of all flows"""

    model = FlowStageBinding
    permission_required = "passbook_flows.view_flowstagebinding"
    paginate_by = 10
    ordering = ["order", "flow"]
    template_name = "administration/stage_binding/list.html"


class StageBindingCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new StageBinding"""

    model = FlowStageBinding
    permission_required = "passbook_flows.add_flowstagebinding"
    form_class = FlowStageBindingForm

    template_name = "generic/create.html"
    success_url = reverse_lazy("passbook_admin:flows")
    success_message = _("Successfully created StageBinding")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        form_cls = self.get_form_class()
        if hasattr(form_cls, "template_name"):
            kwargs["base_template"] = form_cls.template_name
        return kwargs


class StageBindingUpdateView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """Update FlowStageBinding"""

    model = FlowStageBinding
    permission_required = "passbook_flows.change_flowstagebinding"
    form_class = FlowStageBindingForm

    template_name = "generic/update.html"
    success_url = reverse_lazy("passbook_admin:flows")
    success_message = _("Successfully updated StageBinding")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        form_cls = self.get_form_class()
        if hasattr(form_cls, "template_name"):
            kwargs["base_template"] = form_cls.template_name
        return kwargs


class StageBindingDeleteView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    """Delete FlowStageBinding"""

    model = FlowStageBinding
    permission_required = "passbook_flows.delete_flowstagebinding"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("passbook_admin:flows")
    success_message = _("Successfully deleted FlowStageBinding")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)
