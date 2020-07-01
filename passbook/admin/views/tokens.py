"""passbook Token administration"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import DeleteView, ListView
from guardian.mixins import PermissionListMixin, PermissionRequiredMixin

from passbook.core.models import Token


class TokenListView(LoginRequiredMixin, PermissionListMixin, ListView):
    """Show list of all tokens"""

    model = Token
    permission_required = "passbook_core.view_token"
    ordering = "expires"
    paginate_by = 40
    template_name = "administration/token/list.html"


class TokenDeleteView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    """Delete token"""

    model = Token
    permission_required = "passbook_core.delete_token"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("passbook_admin:tokens")
    success_message = _("Successfully deleted Token")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)
