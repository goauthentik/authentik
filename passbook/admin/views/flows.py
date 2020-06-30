"""passbook Flow administration"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpRequest, HttpResponse
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import DeleteView, DetailView, ListView, UpdateView
from guardian.mixins import PermissionListMixin, PermissionRequiredMixin

from passbook.flows.forms import FlowForm
from passbook.flows.models import Flow
from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER
from passbook.flows.views import SESSION_KEY_PLAN, FlowPlanner
from passbook.lib.utils.urls import redirect_with_qs
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


class FlowDebugExecuteView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Debug exectue flow, setting the current user as pending user"""

    model = Flow
    permission_required = "passbook_flows.view_flow"

    # pylint: disable=unused-argument
    def get(self, request: HttpRequest, pk: str) -> HttpResponse:
        """Debug exectue flow, setting the current user as pending user"""
        flow: Flow = self.get_object()
        planner = FlowPlanner(flow)
        planner.use_cache = False
        plan = planner.plan(self.request, {PLAN_CONTEXT_PENDING_USER: request.user})
        self.request.session[SESSION_KEY_PLAN] = plan
        return redirect_with_qs(
            "passbook_flows:flow-executor-shell", self.request.GET, flow_slug=flow.slug,
        )


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
