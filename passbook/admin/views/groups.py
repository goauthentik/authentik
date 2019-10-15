"""passbook Group administration"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import \
    PermissionRequiredMixin as DjangoPermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import DeleteView, ListView, UpdateView
from guardian.mixins import PermissionListMixin, PermissionRequiredMixin

from passbook.core.forms.groups import GroupForm
from passbook.core.models import Group
from passbook.lib.views import CreateAssignPermView


class GroupListView(LoginRequiredMixin, PermissionListMixin, ListView):
    """Show list of all groups"""

    model = Group
    permission_required = 'passbook_core.view_group'
    ordering = 'name'
    paginate_by = 40
    template_name = 'administration/group/list.html'


class GroupCreateView(SuccessMessageMixin, LoginRequiredMixin,
                      DjangoPermissionRequiredMixin, CreateAssignPermView):
    """Create new Group"""

    model = Group
    form_class = GroupForm
    permission_required = 'passbook_core.add_group'
    permissions = [
        'passbook_core.view_group',
        'passbook_core.change_group',
        'passbook_core.delete_group',
    ]
    template_name = 'generic/create.html'
    success_url = reverse_lazy('passbook_admin:groups')
    success_message = _('Successfully created Group')

    def get_context_data(self, **kwargs):
        kwargs['type'] = 'Group'
        return super().get_context_data(**kwargs)


class GroupUpdateView(SuccessMessageMixin, LoginRequiredMixin,
                      PermissionRequiredMixin, UpdateView):
    """Update group"""

    model = Group
    form_class = GroupForm
    permission_required = 'passbook_core.change_group'

    template_name = 'generic/update.html'
    success_url = reverse_lazy('passbook_admin:groups')
    success_message = _('Successfully updated Group')


class GroupDeleteView(SuccessMessageMixin, LoginRequiredMixin, DeleteView):
    """Delete group"""

    model = Group

    template_name = 'generic/delete.html'
    success_url = reverse_lazy('passbook_admin:groups')
    success_message = _('Successfully deleted Group')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)
