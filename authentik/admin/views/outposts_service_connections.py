"""authentik OutpostServiceConnection administration"""
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
from authentik.outposts.models import OutpostServiceConnection


class OutpostServiceConnectionListView(
    LoginRequiredMixin,
    PermissionListMixin,
    UserPaginateListMixin,
    SearchListMixin,
    InheritanceListView,
):
    """Show list of all outpost-service-connections"""

    model = OutpostServiceConnection
    permission_required = "authentik_outposts.add_outpostserviceconnection"
    template_name = "administration/outpost_service_connection/list.html"
    ordering = "pk"
    search_fields = ["pk", "name"]


class OutpostServiceConnectionCreateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    InheritanceCreateView,
):
    """Create new OutpostServiceConnection"""

    model = OutpostServiceConnection
    permission_required = "authentik_outposts.add_outpostserviceconnection"

    template_name = "generic/create.html"
    success_url = reverse_lazy("authentik_admin:outpost-service-connections")
    success_message = _("Successfully created OutpostServiceConnection")


class OutpostServiceConnectionUpdateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    InheritanceUpdateView,
):
    """Update outpostserviceconnection"""

    model = OutpostServiceConnection
    permission_required = "authentik_outposts.change_outpostserviceconnection"

    template_name = "generic/update.html"
    success_url = reverse_lazy("authentik_admin:outpost-service-connections")
    success_message = _("Successfully updated OutpostServiceConnection")


class OutpostServiceConnectionDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView
):
    """Delete outpostserviceconnection"""

    model = OutpostServiceConnection
    permission_required = "authentik_outposts.delete_outpostserviceconnection"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("authentik_admin:outpost-service-connections")
    success_message = _("Successfully deleted OutpostServiceConnection")
