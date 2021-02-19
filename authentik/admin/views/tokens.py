"""authentik Token administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext as _
from guardian.mixins import PermissionRequiredMixin

from authentik.admin.views.utils import DeleteMessageView
from authentik.core.models import Token


class TokenDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView):
    """Delete token"""

    model = Token
    permission_required = "authentik_core.delete_token"

    template_name = "generic/delete.html"
    success_url = "/"
    success_message = _("Successfully deleted Token")
