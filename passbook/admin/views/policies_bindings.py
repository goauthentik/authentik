"""passbook PolicyBinding administration"""
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
from passbook.lib.views import CreateAssignPermView
from passbook.policies.forms import PolicyBindingForm
from passbook.policies.models import PolicyBinding


class PolicyBindingListView(LoginRequiredMixin, PermissionListMixin, ListView):
    """Show list of all policies"""

    model = PolicyBinding
    permission_required = "passbook_policies.view_policybinding"
    paginate_by = 10
    ordering = ["order", "target"]
    template_name = "administration/policybinding/list.html"


class PolicyBindingCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new PolicyBinding"""

    model = PolicyBinding
    permission_required = "passbook_policies.add_policybinding"
    form_class = PolicyBindingForm

    template_name = "generic/create.html"
    success_url = reverse_lazy("passbook_admin:policies-bindings")
    success_message = _("Successfully created PolicyBinding")


class PolicyBindingUpdateView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """Update policybinding"""

    model = PolicyBinding
    permission_required = "passbook_policies.change_policybinding"
    form_class = PolicyBindingForm

    template_name = "generic/update.html"
    success_url = reverse_lazy("passbook_admin:policies-bindings")
    success_message = _("Successfully updated PolicyBinding")


class PolicyBindingDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView
):
    """Delete policybinding"""

    model = PolicyBinding
    permission_required = "passbook_policies.delete_policybinding"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("passbook_admin:policies-bindings")
    success_message = _("Successfully deleted PolicyBinding")
