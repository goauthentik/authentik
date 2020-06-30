"""passbook Event administration"""
from django.views.generic import ListView
from guardian.mixins import PermissionListMixin

from passbook.audit.models import Event


class EventListView(PermissionListMixin, ListView):
    """Show list of all invitations"""

    model = Event
    template_name = "audit/list.html"
    permission_required = "passbook_audit.view_event"
    ordering = "-created"
    paginate_by = 20
