"""passbook core user views"""
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import reverse
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import DeleteView, UpdateView

from passbook.core.forms.users import UserDetailForm


class UserSettingsView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    """Update User settings"""

    template_name = "user/settings.html"
    form_class = UserDetailForm

    success_message = _("Successfully updated user.")
    success_url = reverse_lazy("passbook_core:user-settings")

    def get_object(self):
        return self.request.user


class UserDeleteView(LoginRequiredMixin, DeleteView):
    """Delete user account"""

    template_name = "generic/delete.html"

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        messages.success(self.request, _("Successfully deleted user."))
        logout(self.request)
        return reverse("passbook_flows:default-auth")
