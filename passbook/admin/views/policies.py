"""passbook Policy administration"""
from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import FormView
from django.views.generic.detail import DetailView
from guardian.mixins import PermissionListMixin, PermissionRequiredMixin

from passbook.admin.forms.policies import PolicyTestForm
from passbook.admin.views.utils import (
    DeleteMessageView,
    InheritanceCreateView,
    InheritanceListView,
    InheritanceUpdateView, UserPaginateListMixin,
)
from passbook.policies.models import Policy, PolicyBinding
from passbook.policies.process import PolicyProcess, PolicyRequest


class PolicyListView(LoginRequiredMixin, PermissionListMixin, UserPaginateListMixin, InheritanceListView):
    """Show list of all policies"""

    model = Policy
    permission_required = "passbook_policies.view_policy"
    ordering = "name"
    template_name = "administration/policy/list.html"


class PolicyCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    InheritanceCreateView,
):
    """Create new Policy"""

    model = Policy
    permission_required = "passbook_policies.add_policy"

    template_name = "generic/create.html"
    success_url = reverse_lazy("passbook_admin:policies")
    success_message = _("Successfully created Policy")


class PolicyUpdateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    InheritanceUpdateView,
):
    """Update policy"""

    model = Policy
    permission_required = "passbook_policies.change_policy"

    template_name = "generic/update.html"
    success_url = reverse_lazy("passbook_admin:policies")
    success_message = _("Successfully updated Policy")


class PolicyDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView):
    """Delete policy"""

    model = Policy
    permission_required = "passbook_policies.delete_policy"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("passbook_admin:policies")
    success_message = _("Successfully deleted Policy")


class PolicyTestView(LoginRequiredMixin, DetailView, PermissionRequiredMixin, FormView):
    """View to test policy(s)"""

    model = Policy
    form_class = PolicyTestForm
    permission_required = "passbook_policies.view_policy"
    template_name = "administration/policy/test.html"
    object = None

    def get_object(self, queryset=None) -> QuerySet:
        return (
            Policy.objects.filter(pk=self.kwargs.get("pk")).select_subclasses().first()
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs["policy"] = self.get_object()
        return super().get_context_data(**kwargs)

    def post(self, *args, **kwargs) -> HttpResponse:
        self.object = self.get_object()
        return super().post(*args, **kwargs)

    def form_valid(self, form: PolicyTestForm) -> HttpResponse:
        policy = self.get_object()
        user = form.cleaned_data.get("user")

        p_request = PolicyRequest(user)
        p_request.http_request = self.request
        p_request.context = form.cleaned_data

        proc = PolicyProcess(PolicyBinding(policy=policy), p_request, None)
        result = proc.execute()
        if result.passing:
            messages.success(self.request, _("User successfully passed policy."))
        else:
            messages.error(self.request, _("User didn't pass policy."))
        return self.render_to_response(self.get_context_data(form=form, result=result))
