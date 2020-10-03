"""passbook Token administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import ListView
from guardian.mixins import PermissionListMixin, PermissionRequiredMixin

from passbook.admin.views.utils import (
    DeleteMessageView,
    SearchListMixin,
    UserPaginateListMixin,
)
from passbook.core.models import Token


class TokenListView(
    LoginRequiredMixin,
    PermissionListMixin,
    UserPaginateListMixin,
    SearchListMixin,
    ListView,
):
    """Show list of all tokens"""

    model = Token
    permission_required = "passbook_core.view_token"
    ordering = "expires"
    template_name = "administration/token/list.html"
    search_fields = [
        "intent",
        "user__username",
        "description",
    ]


class TokenDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView):
    """Delete token"""

    model = Token
    permission_required = "passbook_core.delete_token"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("passbook_admin:tokens")
    success_message = _("Successfully deleted Token")
