"""passbook Group administration"""
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from passbook.admin.mixins import AdminRequiredMixin
from passbook.core.forms.groups import GroupForm
from passbook.core.models import Group


class GroupListView(AdminRequiredMixin, ListView):
    """Show list of all groups"""

    model = Group
    ordering = 'name'
    paginate_by = 40
    template_name = 'administration/group/list.html'


class GroupCreateView(SuccessMessageMixin, AdminRequiredMixin, CreateView):
    """Create new Group"""

    form_class = GroupForm

    template_name = 'generic/create.html'
    success_url = reverse_lazy('passbook_admin:groups')
    success_message = _('Successfully created Group')

    def get_context_data(self, **kwargs):
        kwargs['type'] = 'Group'
        return super().get_context_data(**kwargs)


class GroupUpdateView(SuccessMessageMixin, AdminRequiredMixin, UpdateView):
    """Update group"""

    model = Group
    form_class = GroupForm

    template_name = 'generic/update.html'
    success_url = reverse_lazy('passbook_admin:groups')
    success_message = _('Successfully updated Group')


class GroupDeleteView(SuccessMessageMixin, AdminRequiredMixin, DeleteView):
    """Delete group"""

    model = Group

    template_name = 'generic/delete.html'
    success_url = reverse_lazy('passbook_admin:groups')
    success_message = _('Successfully deleted Group')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)
