"""passbook User administration"""
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import DeleteView, ListView, UpdateView

from passbook.admin.mixins import AdminRequiredMixin
from passbook.core.forms.users import UserDetailForm
from passbook.core.models import User


class UserListView(AdminRequiredMixin, ListView):
    """Show list of all users"""

    model = User
    template_name = 'administration/user/list.html'


class UserUpdateView(SuccessMessageMixin, AdminRequiredMixin, UpdateView):
    """Update user"""

    model = User
    form_class = UserDetailForm

    template_name = 'generic/update.html'
    success_url = reverse_lazy('passbook_admin:users')
    success_message = _('Successfully updated User')


class UserDeleteView(SuccessMessageMixin, AdminRequiredMixin, DeleteView):
    """Delete user"""

    model = User

    success_url = reverse_lazy('passbook_admin:users')
    success_message = _('Successfully updated User')
