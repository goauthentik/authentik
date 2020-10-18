"""passbook core user views"""
from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models.query import QuerySet
from django.http.response import HttpResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import ListView, UpdateView
from guardian.mixins import PermissionListMixin, PermissionRequiredMixin
from guardian.shortcuts import get_objects_for_user

from passbook.admin.views.utils import (
    DeleteMessageView,
    SearchListMixin,
    UserPaginateListMixin,
)
from passbook.core.forms.token import UserTokenForm
from passbook.core.forms.users import UserDetailForm
from passbook.core.models import Token, TokenIntents
from passbook.flows.models import Flow, FlowDesignation
from passbook.lib.views import CreateAssignPermView


class UserSettingsView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    """Update User settings"""

    template_name = "user/settings.html"
    form_class = UserDetailForm

    success_message = _("Successfully updated user.")
    success_url = reverse_lazy("passbook_core:user-settings")

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs = super().get_context_data(**kwargs)
        unenrollment_flow = Flow.with_policy(
            self.request, designation=FlowDesignation.UNRENOLLMENT
        )
        kwargs["unenrollment_enabled"] = bool(unenrollment_flow)
        return kwargs


class TokenListView(
    LoginRequiredMixin,
    PermissionListMixin,
    UserPaginateListMixin,
    SearchListMixin,
    ListView,
):
    """Show list of all tokens"""

    model = Token
    ordering = "expires"
    permission_required = "passbook_core.view_token"

    template_name = "user/token_list.html"
    search_fields = [
        "identifier",
        "intent",
        "description",
    ]

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(intent=TokenIntents.INTENT_API)


class TokenCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new Token"""

    model = Token
    form_class = UserTokenForm
    permission_required = "passbook_core.add_token"

    template_name = "generic/create.html"
    success_url = reverse_lazy("passbook_core:user-tokens")
    success_message = _("Successfully created Token")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs = super().get_context_data(**kwargs)
        kwargs["container_template"] = "user/base.html"
        return kwargs

    def form_valid(self, form: UserTokenForm) -> HttpResponse:
        form.instance.user = self.request.user
        form.instance.intent = TokenIntents.INTENT_API
        return super().form_valid(form)


class TokenUpdateView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """Update token"""

    model = Token
    form_class = UserTokenForm
    permission_required = "passbook_core.update_token"
    template_name = "generic/update.html"
    success_url = reverse_lazy("passbook_core:user-tokens")
    success_message = _("Successfully updated Token")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs = super().get_context_data(**kwargs)
        kwargs["container_template"] = "user/base.html"
        return kwargs

    def get_object(self) -> Token:
        identifier = self.kwargs.get("identifier")
        return get_objects_for_user(
            self.request.user, "passbook_core.update_token", self.model
        ).filter(intent=TokenIntents.INTENT_API, identifier=identifier)


class TokenDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView):
    """Delete token"""

    model = Token
    permission_required = "passbook_core.delete_token"
    template_name = "generic/delete.html"
    success_url = reverse_lazy("passbook_core:user-tokens")
    success_message = _("Successfully deleted Token")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs = super().get_context_data(**kwargs)
        kwargs["container_template"] = "user/base.html"
        return kwargs
