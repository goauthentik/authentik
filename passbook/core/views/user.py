"""passbook core user views"""
from django.contrib import messages
from django.contrib.auth import logout
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import DeleteView, UpdateView

from passbook.core.forms.users import UserDetailForm


class UserSettingsView(UpdateView):
    """Update User settings"""
    template_name = 'user/settings.html'
    form_class = UserDetailForm

    def get_object(self):
        return self.request.user

class UserDeleteView(DeleteView):
    """Delete user account"""

    template_name = 'generic/delete.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        messages.success(self.request, _('Successfully deleted user.'))
        logout(self.request)
        return reverse('passbook_core:auth-login')
