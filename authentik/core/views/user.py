"""authentik core user views"""
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.http.response import HttpResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import UpdateView
from django.views.generic.base import TemplateView
from guardian.mixins import PermissionRequiredMixin
from guardian.shortcuts import get_objects_for_user

from authentik.core.forms.token import UserTokenForm
from authentik.core.models import Token, TokenIntents
from authentik.flows.models import Flow, FlowDesignation
from authentik.lib.views import CreateAssignPermView


class TokenCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new Token"""

    model = Token
    form_class = UserTokenForm
    permission_required = "authentik_core.add_token"

    template_name = "generic/create.html"
    success_url = "/"
    success_message = _("Successfully created Token")

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
    permission_required = "authentik_core.change_token"
    template_name = "generic/update.html"
    success_url = "/"
    success_message = _("Successfully updated Token")

    def get_object(self) -> Token:
        identifier = self.kwargs.get("identifier")
        return (
            get_objects_for_user(
                self.request.user, self.permission_required, self.model
            )
            .filter(intent=TokenIntents.INTENT_API, identifier=identifier)
            .first()
        )
