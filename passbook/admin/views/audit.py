"""passbook AuditEntry administration"""
from django.views.generic import ListView
from guardian.mixins import PermissionListMixin

from passbook.audit.models import AuditEntry


class AuditEntryListView(PermissionListMixin, ListView):
    """Show list of all invitations"""

    model = AuditEntry
    template_name = 'administration/audit/list.html'
    permission_required = 'passbook_audit.view_auditentry'
    ordering = '-created'
    paginate_by = 10

    def get_queryset(self):
        return AuditEntry.objects.all().order_by('-created')
