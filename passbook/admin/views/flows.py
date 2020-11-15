"""passbook Flow administration"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import DetailView, FormView, ListView, UpdateView
from guardian.mixins import PermissionListMixin, PermissionRequiredMixin

from passbook.admin.views.utils import (
    BackSuccessUrlMixin,
    DeleteMessageView,
    SearchListMixin,
    UserPaginateListMixin,
)
from passbook.flows.forms import FlowForm, FlowImportForm
from passbook.flows.models import Flow
from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER
from passbook.flows.transfer.common import DataclassEncoder
from passbook.flows.transfer.exporter import FlowExporter
from passbook.flows.transfer.importer import FlowImporter
from passbook.flows.views import SESSION_KEY_PLAN, FlowPlanner
from passbook.lib.utils.urls import redirect_with_qs
from passbook.lib.views import CreateAssignPermView


class FlowListView(
    LoginRequiredMixin,
    PermissionListMixin,
    UserPaginateListMixin,
    SearchListMixin,
    ListView,
):
    """Show list of all flows"""

    model = Flow
    permission_required = "passbook_flows.view_flow"
    ordering = "name"
    template_name = "administration/flow/list.html"
    search_fields = ["name", "slug", "designation", "title"]


class FlowCreateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
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


class FlowUpdateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    """Update flow"""

    model = Flow
    form_class = FlowForm
    permission_required = "passbook_flows.change_flow"

    template_name = "generic/update.html"
    success_url = reverse_lazy("passbook_admin:flows")
    success_message = _("Successfully updated Flow")


class FlowDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView):
    """Delete flow"""

    model = Flow
    permission_required = "passbook_flows.delete_flow"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("passbook_admin:flows")
    success_message = _("Successfully deleted Flow")


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
            "passbook_flows:flow-executor-shell",
            self.request.GET,
            flow_slug=flow.slug,
        )


class FlowImportView(LoginRequiredMixin, FormView):
    """Import flow from JSON Export; only allowed for superusers
    as these flows can contain python code"""

    form_class = FlowImportForm
    template_name = "administration/flow/import.html"
    success_url = reverse_lazy("passbook_admin:flows")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: FlowImportForm) -> HttpResponse:
        importer = FlowImporter(form.cleaned_data["flow"].read().decode())
        successful = importer.apply()
        if not successful:
            messages.error(self.request, _("Failed to import flow."))
        else:
            messages.success(self.request, _("Successfully imported flow."))
        return super().form_valid(form)


class FlowExportView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Export Flow"""

    model = Flow
    permission_required = "passbook_flows.export_flow"

    # pylint: disable=unused-argument
    def get(self, request: HttpRequest, pk: str) -> HttpResponse:
        """Debug exectue flow, setting the current user as pending user"""
        flow: Flow = self.get_object()
        exporter = FlowExporter(flow)
        response = JsonResponse(exporter.export(), encoder=DataclassEncoder, safe=False)
        response["Content-Disposition"] = f'attachment; filename="{flow.slug}.pbflow"'
        return response
