"""passbook Group administration"""
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
from passbook.core.forms.groups import GroupForm
from passbook.core.models import Group
from passbook.lib.views import CreateAssignPermView


class GroupListView(LoginRequiredMixin, PermissionListMixin, ListView):
    """Show list of all groups"""

    model = Group
    permission_required = "passbook_core.view_group"
    ordering = "name"
    paginate_by = 40
    template_name = "administration/group/list.html"


class GroupCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new Group"""

    model = Group
    form_class = GroupForm
    permission_required = "passbook_core.add_group"

    template_name = "generic/create.html"
    success_url = reverse_lazy("passbook_admin:groups")
    success_message = _("Successfully created Group")


class GroupUpdateView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """Update group"""

    model = Group
    form_class = GroupForm
    permission_required = "passbook_core.change_group"

    template_name = "generic/update.html"
    success_url = reverse_lazy("passbook_admin:groups")
    success_message = _("Successfully updated Group")


class GroupDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView):
    """Delete group"""

    model = Group
    permission_required = "passbook_flows.delete_group"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("passbook_admin:groups")
    success_message = _("Successfully deleted Group")
