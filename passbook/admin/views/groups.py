"""passbook Group administration"""
from django.views.generic import ListView

from passbook.admin.mixins import AdminRequiredMixin
from passbook.core.models import Group


class GroupListView(AdminRequiredMixin, ListView):
    """Show list of all invitations"""

    model = Group
    template_name = 'administration/groups/list.html'
