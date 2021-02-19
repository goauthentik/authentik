"""authentik PolicyBinding administration"""
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Max
from django.utils.translation import gettext as _
from django.views.generic import UpdateView
from guardian.mixins import PermissionRequiredMixin

from authentik.admin.views.utils import BackSuccessUrlMixin, DeleteMessageView
from authentik.lib.views import CreateAssignPermView
from authentik.policies.forms import PolicyBindingForm
from authentik.policies.models import PolicyBinding, PolicyBindingModel


class PolicyBindingCreateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new PolicyBinding"""

    model = PolicyBinding
    permission_required = "authentik_policies.add_policybinding"
    form_class = PolicyBindingForm

    template_name = "generic/create.html"
    success_url = "/"
    success_message = _("Successfully created PolicyBinding")

    def get_initial(self) -> dict[str, Any]:
        if "target" in self.request.GET:
            initial_target_pk = self.request.GET["target"]
            targets = PolicyBindingModel.objects.filter(
                pk=initial_target_pk
            ).select_subclasses()
            if not targets.exists():
                return {}
            max_order = PolicyBinding.objects.filter(target=targets.first()).aggregate(
                Max("order")
            )["order__max"]
            if not isinstance(max_order, int):
                max_order = -1
            return {"target": targets.first(), "order": max_order + 1}
        return super().get_initial()


class PolicyBindingUpdateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    """Update policybinding"""

    model = PolicyBinding
    permission_required = "authentik_policies.change_policybinding"
    form_class = PolicyBindingForm

    template_name = "generic/update.html"
    success_url = "/"
    success_message = _("Successfully updated PolicyBinding")


class PolicyBindingDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView
):
    """Delete policybinding"""

    model = PolicyBinding
    permission_required = "authentik_policies.delete_policybinding"

    template_name = "generic/delete.html"
    success_url = "/"
    success_message = _("Successfully deleted PolicyBinding")
