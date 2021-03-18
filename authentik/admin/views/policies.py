"""authentik Policy administration"""
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import FormView
from django.views.generic.detail import DetailView
from guardian.mixins import PermissionRequiredMixin

from authentik.admin.forms.policies import PolicyTestForm
from authentik.admin.views.utils import InheritanceCreateView, InheritanceUpdateView
from authentik.policies.models import Policy, PolicyBinding
from authentik.policies.process import PolicyProcess, PolicyRequest


class PolicyCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    InheritanceCreateView,
):
    """Create new Policy"""

    model = Policy
    permission_required = "authentik_policies.add_policy"

    template_name = "generic/create.html"
    success_url = reverse_lazy("authentik_core:shell")
    success_message = _("Successfully created Policy")


class PolicyUpdateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    InheritanceUpdateView,
):
    """Update policy"""

    model = Policy
    permission_required = "authentik_policies.change_policy"

    template_name = "generic/update.html"
    success_url = reverse_lazy("authentik_core:shell")
    success_message = _("Successfully updated Policy")


class PolicyTestView(LoginRequiredMixin, DetailView, PermissionRequiredMixin, FormView):
    """View to test policy(s)"""

    model = Policy
    form_class = PolicyTestForm
    permission_required = "authentik_policies.view_policy"
    template_name = "administration/policy/test.html"
    object = None

    def get_object(self, queryset=None) -> Policy:
        return (
            Policy.objects.filter(pk=self.kwargs.get("pk")).select_subclasses().first()
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        kwargs["policy"] = self.get_object()
        return super().get_context_data(**kwargs)

    def post(self, *args, **kwargs) -> HttpResponse:
        self.object = self.get_object()
        return super().post(*args, **kwargs)

    def form_valid(self, form: PolicyTestForm) -> HttpResponse:
        policy = self.get_object()
        user = form.cleaned_data.get("user")

        p_request = PolicyRequest(user)
        p_request.debug = True
        p_request.set_http_request(self.request)
        p_request.context = form.cleaned_data.get("context", {})

        proc = PolicyProcess(PolicyBinding(policy=policy), p_request, None)
        result = proc.execute()
        context = self.get_context_data(form=form)
        context["result"] = result
        return self.render_to_response(context)
