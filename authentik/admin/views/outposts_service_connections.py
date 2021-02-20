"""authentik OutpostServiceConnection administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from guardian.mixins import PermissionRequiredMixin

from authentik.admin.views.utils import (
    DeleteMessageView,
    InheritanceCreateView,
    InheritanceUpdateView,
)
from authentik.outposts.models import OutpostServiceConnection


class OutpostServiceConnectionCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    InheritanceCreateView,
):
    """Create new OutpostServiceConnection"""

    model = OutpostServiceConnection
    permission_required = "authentik_outposts.add_outpostserviceconnection"

    template_name = "generic/create.html"
    success_url = reverse_lazy("authentik_core:shell")
    success_message = _("Successfully created Outpost Service Connection")


class OutpostServiceConnectionUpdateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    InheritanceUpdateView,
):
    """Update outpostserviceconnection"""

    model = OutpostServiceConnection
    permission_required = "authentik_outposts.change_outpostserviceconnection"

    template_name = "generic/update.html"
    success_url = reverse_lazy("authentik_core:shell")
    success_message = _("Successfully updated Outpost Service Connection")


class OutpostServiceConnectionDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView
):
    """Delete outpostserviceconnection"""

    model = OutpostServiceConnection
    permission_required = "authentik_outposts.delete_outpostserviceconnection"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("authentik_core:shell")
    success_message = _("Successfully deleted Outpost Service Connection")
