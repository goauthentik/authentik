"""authentik StageBinding administration"""
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Max
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import UpdateView
from guardian.mixins import PermissionRequiredMixin

from authentik.admin.views.utils import DeleteMessageView
from authentik.flows.forms import FlowStageBindingForm
from authentik.flows.models import Flow, FlowStageBinding
from authentik.lib.views import CreateAssignPermView


class StageBindingCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new StageBinding"""

    model = FlowStageBinding
    permission_required = "authentik_flows.add_flowstagebinding"
    form_class = FlowStageBindingForm

    template_name = "generic/create.html"
    success_url = reverse_lazy("authentik_core:shell")
    success_message = _("Successfully created StageBinding")

    def get_initial(self) -> dict[str, Any]:
        if "target" in self.request.GET:
            initial_target_pk = self.request.GET["target"]
            targets = Flow.objects.filter(pk=initial_target_pk).select_subclasses()
            if not targets.exists():
                return {}
            max_order = FlowStageBinding.objects.filter(
                target=targets.first()
            ).aggregate(Max("order"))["order__max"]
            if not isinstance(max_order, int):
                max_order = -1
            return {"target": targets.first(), "order": max_order + 1}
        return super().get_initial()


class StageBindingUpdateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    """Update FlowStageBinding"""

    model = FlowStageBinding
    permission_required = "authentik_flows.change_flowstagebinding"
    form_class = FlowStageBindingForm

    template_name = "generic/update.html"
    success_url = reverse_lazy("authentik_core:shell")
    success_message = _("Successfully updated StageBinding")


class StageBindingDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView
):
    """Delete FlowStageBinding"""

    model = FlowStageBinding
    permission_required = "authentik_flows.delete_flowstagebinding"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("authentik_core:shell")
    success_message = _("Successfully deleted FlowStageBinding")
