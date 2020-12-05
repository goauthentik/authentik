"""authentik Stage administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from guardian.mixins import PermissionListMixin, PermissionRequiredMixin

from authentik.admin.views.utils import (
    BackSuccessUrlMixin,
    DeleteMessageView,
    InheritanceCreateView,
    InheritanceListView,
    InheritanceUpdateView,
    SearchListMixin,
    UserPaginateListMixin,
)
from authentik.flows.models import Stage


class StageListView(
    LoginRequiredMixin,
    PermissionListMixin,
    UserPaginateListMixin,
    SearchListMixin,
    InheritanceListView,
):
    """Show list of all stages"""

    model = Stage
    template_name = "administration/stage/list.html"
    permission_required = "authentik_flows.view_stage"
    ordering = "name"
    search_fields = ["name"]


class StageCreateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    InheritanceCreateView,
):
    """Create new Stage"""

    model = Stage
    template_name = "generic/create.html"
    permission_required = "authentik_flows.add_stage"

    success_url = reverse_lazy("authentik_admin:stages")
    success_message = _("Successfully created Stage")


class StageUpdateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    InheritanceUpdateView,
):
    """Update stage"""

    model = Stage
    permission_required = "authentik_flows.update_application"
    template_name = "generic/update.html"
    success_url = reverse_lazy("authentik_admin:stages")
    success_message = _("Successfully updated Stage")


class StageDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView):
    """Delete stage"""

    model = Stage
    template_name = "generic/delete.html"
    permission_required = "authentik_flows.delete_stage"
    success_url = reverse_lazy("authentik_admin:stages")
    success_message = _("Successfully deleted Stage")
