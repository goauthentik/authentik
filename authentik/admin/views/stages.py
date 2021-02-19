"""authentik Stage administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import gettext as _
from guardian.mixins import PermissionRequiredMixin

from authentik.admin.views.utils import (
    BackSuccessUrlMixin,
    DeleteMessageView,
    InheritanceCreateView,
    InheritanceUpdateView,
)
from authentik.flows.models import Stage


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

    success_url = "/"
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
    success_url = "/"
    success_message = _("Successfully updated Stage")


class StageDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView):
    """Delete stage"""

    model = Stage
    template_name = "generic/delete.html"
    permission_required = "authentik_flows.delete_stage"
    success_url = "/"
    success_message = _("Successfully deleted Stage")
