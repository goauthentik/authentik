"""passbook Event administration"""
from django.views.generic import ListView
from guardian.mixins import PermissionListMixin

from passbook.audit.models import Event


class EventListView(PermissionListMixin, ListView):
    """Show list of all invitations"""

    model = Event
    template_name = "administration/audit/list.html"
    permission_required = "passbook_audit.view_event"
    ordering = "-created"
    paginate_by = 10

    def get_queryset(self):
        return Event.objects.all().order_by("-created")
