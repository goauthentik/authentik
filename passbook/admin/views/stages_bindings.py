"""passbook StageBinding administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import ListView, UpdateView
from guardian.mixins import PermissionListMixin, PermissionRequiredMixin

from passbook.admin.views.utils import DeleteMessageView
from passbook.flows.forms import FlowStageBindingForm
from passbook.flows.models import FlowStageBinding
from passbook.lib.views import CreateAssignPermView


class StageBindingListView(LoginRequiredMixin, PermissionListMixin, ListView):
    """Show list of all flows"""

    model = FlowStageBinding
    permission_required = "passbook_flows.view_flowstagebinding"
    paginate_by = 10
    ordering = ["flow", "order"]
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
    success_url = reverse_lazy("passbook_admin:stage-bindings")
    success_message = _("Successfully created StageBinding")


class StageBindingUpdateView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """Update FlowStageBinding"""

    model = FlowStageBinding
    permission_required = "passbook_flows.change_flowstagebinding"
    form_class = FlowStageBindingForm

    template_name = "generic/update.html"
    success_url = reverse_lazy("passbook_admin:stage-bindings")
    success_message = _("Successfully updated StageBinding")


class StageBindingDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView
):
    """Delete FlowStageBinding"""

    model = FlowStageBinding
    permission_required = "passbook_flows.delete_flowstagebinding"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("passbook_admin:stage-bindings")
    success_message = _("Successfully deleted FlowStageBinding")
