"""authentik Group administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import gettext as _
from django.views.generic import UpdateView
from guardian.mixins import PermissionRequiredMixin

from authentik.admin.views.utils import DeleteMessageView
from authentik.core.forms.groups import GroupForm
from authentik.core.models import Group
from authentik.lib.views import CreateAssignPermView


class GroupCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new Group"""

    model = Group
    form_class = GroupForm
    permission_required = "authentik_core.add_group"

    template_name = "generic/create.html"
    success_url = "/"
    success_message = _("Successfully created Group")


class GroupUpdateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    """Update group"""

    model = Group
    form_class = GroupForm
    permission_required = "authentik_core.change_group"

    template_name = "generic/update.html"
    success_url = "/"
    success_message = _("Successfully updated Group")


class GroupDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView):
    """Delete group"""

    model = Group
    permission_required = "authentik_flows.delete_group"

    template_name = "generic/delete.html"
    success_url = "/"
    success_message = _("Successfully deleted Group")
