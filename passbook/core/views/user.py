"""passbook core user views"""
from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.forms.utils import ErrorList
from django.shortcuts import redirect, reverse
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import DeleteView, FormView, UpdateView

from passbook.core.forms.users import PasswordChangeForm, UserDetailForm
from passbook.lib.config import CONFIG


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
        return reverse("passbook_core:auth-login")


class UserChangePasswordView(LoginRequiredMixin, FormView):
    """View for users to update their password"""

    form_class = PasswordChangeForm
    template_name = "login/form_with_user.html"

    def form_valid(self, form: PasswordChangeForm):
        # TODO: Rewrite to flow
        try:
            # user.set_password checks against Policies so we don't need to manually do it here
            self.request.user.set_password(form.cleaned_data.get("password"))
            self.request.user.save()
            update_session_auth_hash(self.request, self.request.user)
            messages.success(self.request, _("Successfully changed password"))
        except ValueError:
            # Manually inject error into form
            # pylint: disable=protected-access
            errors = form._errors.setdefault("password_repeat", ErrorList(""))
            # pylint: disable=protected-access
            errors = form._errors.setdefault("password", ErrorList())
            errors.append("foo")
            return self.form_invalid(form)
        return redirect("passbook_core:overview")

    def get_context_data(self, **kwargs):
        kwargs["config"] = CONFIG.y("passbook")
        kwargs["title"] = _("Change Password")
        kwargs["primary_action"] = _("Change")
        return super().get_context_data(**kwargs)
