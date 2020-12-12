"""authentik PolicyBinding administration"""
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Max, QuerySet
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import ListView, UpdateView
from guardian.mixins import PermissionListMixin, PermissionRequiredMixin
from guardian.shortcuts import get_objects_for_user

from authentik.admin.views.utils import (
    BackSuccessUrlMixin,
    DeleteMessageView,
    UserPaginateListMixin,
)
from authentik.lib.views import CreateAssignPermView
from authentik.policies.forms import PolicyBindingForm
from authentik.policies.models import PolicyBinding, PolicyBindingModel


class PolicyBindingListView(
    LoginRequiredMixin, PermissionListMixin, UserPaginateListMixin, ListView
):
    """Show list of all policies"""

    model = PolicyBinding
    permission_required = "authentik_policies.view_policybinding"
    ordering = ["order", "target"]
    template_name = "administration/policy_binding/list.html"

    def get_queryset(self) -> QuerySet:
        # Since `select_subclasses` does not work with a foreign key, we have to do two queries here
        # First, get all pbm objects that have bindings attached
        objects = (
            get_objects_for_user(
                self.request.user, "authentik_policies.view_policybindingmodel"
            )
            .filter(policies__isnull=False)
            .select_subclasses()
            .select_related()
            .order_by("pk")
        )
        for pbm in objects:
            pbm.bindings = get_objects_for_user(
                self.request.user, self.permission_required
            ).filter(target__pk=pbm.pbm_uuid)
        return objects


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
    success_url = reverse_lazy("authentik_admin:policies-bindings")
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
    success_url = reverse_lazy("authentik_admin:policies-bindings")
    success_message = _("Successfully updated PolicyBinding")


class PolicyBindingDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView
):
    """Delete policybinding"""

    model = PolicyBinding
    permission_required = "authentik_policies.delete_policybinding"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("authentik_admin:policies-bindings")
    success_message = _("Successfully deleted PolicyBinding")
