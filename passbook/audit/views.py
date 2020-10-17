"""passbook Event administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from guardian.mixins import PermissionListMixin

from passbook.admin.views.utils import SearchListMixin, UserPaginateListMixin
from passbook.audit.models import Event


class EventListView(
    PermissionListMixin,
    LoginRequiredMixin,
    SearchListMixin,
    UserPaginateListMixin,
    ListView,
):
    """Show list of all invitations"""

    model = Event
    template_name = "audit/list.html"
    permission_required = "passbook_audit.view_event"
    ordering = "-created"

    search_fields = [
        "user",
        "action",
        "app",
        "context",
        "client_ip",
    ]
