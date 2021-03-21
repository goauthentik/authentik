"""authentik User administration"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.http import urlencode
from django.utils.translation import gettext as _
from django.views.generic import DetailView, UpdateView
from guardian.mixins import PermissionRequiredMixin

from authentik.admin.forms.users import UserForm
from authentik.core.models import Token, User
from authentik.lib.views import CreateAssignPermView


class UserCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create user"""

    model = User
    form_class = UserForm
    permission_required = "authentik_core.add_user"

    template_name = "generic/create.html"
    success_url = reverse_lazy("authentik_core:if-admin")
    success_message = _("Successfully created User")


class UserUpdateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    """Update user"""

    model = User
    form_class = UserForm
    permission_required = "authentik_core.change_user"

    # By default the object's name is user which is used by other checks
    context_object_name = "object"
    template_name = "generic/update.html"
    success_url = reverse_lazy("authentik_core:if-admin")
    success_message = _("Successfully updated User")


class UserPasswordResetView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Get Password reset link for user"""

    model = User
    permission_required = "authentik_core.reset_user_password"

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Create token for user and return link"""
        super().get(request, *args, **kwargs)
        token, __ = Token.objects.get_or_create(
            identifier="password-reset-temp", user=self.object
        )
        querystring = urlencode({"token": token.key})
        link = request.build_absolute_uri(
            reverse_lazy("authentik_flows:default-recovery") + f"?{querystring}"
        )
        messages.success(request, _("Password reset link: %(link)s" % {"link": link}))
        return redirect("/")
