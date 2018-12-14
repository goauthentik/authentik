"""passbook AuditEntry administration"""
from django.views.generic import ListView

from passbook.admin.mixins import AdminRequiredMixin
from passbook.audit.models import AuditEntry


class AuditEntryListView(AdminRequiredMixin, ListView):
    """Show list of all invitations"""

    model = AuditEntry
    template_name = 'administration/audit/list.html'
    paginate_by = 10

    def get_queryset(self):
        return AuditEntry.objects.all().order_by('-created')
