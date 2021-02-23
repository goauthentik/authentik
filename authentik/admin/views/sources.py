"""authentik Source administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import gettext as _
from guardian.mixins import PermissionRequiredMixin

from authentik.admin.views.utils import (
    BackSuccessUrlMixin,
    DeleteMessageView,
    InheritanceCreateView,
    InheritanceUpdateView,
)
from authentik.core.models import Source


class SourceCreateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    InheritanceCreateView,
):
    """Create new Source"""

    model = Source
    permission_required = "authentik_core.add_source"

    success_url = "/"
    template_name = "generic/create.html"
    success_message = _("Successfully created Source")


class SourceUpdateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    InheritanceUpdateView,
):
    """Update source"""

    model = Source
    permission_required = "authentik_core.change_source"

    success_url = "/"
    template_name = "generic/update.html"
    success_message = _("Successfully updated Source")


class SourceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView):
    """Delete source"""

    model = Source
    permission_required = "authentik_core.delete_source"

    success_url = "/"
    template_name = "generic/delete.html"
    success_message = _("Successfully deleted Source")
