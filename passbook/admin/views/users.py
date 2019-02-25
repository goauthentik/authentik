"""passbook User administration"""
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import ugettext as _
from django.views import View
from django.views.generic import DeleteView, ListView, UpdateView

from passbook.admin.mixins import AdminRequiredMixin
from passbook.core.forms.users import UserDetailForm
from passbook.core.models import Nonce, User


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


class UserPasswordResetView(AdminRequiredMixin, View):
    """Get Password reset link for user"""

    # pylint: disable=invalid-name
    def get(self, request, pk):
        """Create nonce for user and return link"""
        user = get_object_or_404(User, pk=pk)
        nonce = Nonce.objects.create(user=user)
        link = request.build_absolute_uri(reverse(
            'passbook_core:auth-password-reset', kwargs={'nonce': nonce.uuid}))
        messages.success(request, _('Password reset link: <pre>%(link)s</pre>' % {'link': link}))
        return redirect('passbook_admin:users')
