"""authentik Provider administration"""
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
from authentik.core.models import Provider


class ProviderCreateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    InheritanceCreateView,
):
    """Create new Provider"""

    model = Provider
    permission_required = "authentik_core.add_provider"

    template_name = "generic/create.html"
    success_message = _("Successfully created Provider")


class ProviderUpdateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    InheritanceUpdateView,
):
    """Update provider"""

    model = Provider
    permission_required = "authentik_core.change_provider"

    template_name = "generic/update.html"
    success_message = _("Successfully updated Provider")


class ProviderDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView
):
    """Delete provider"""

    model = Provider
    permission_required = "authentik_core.delete_provider"

    template_name = "generic/delete.html"
    success_message = _("Successfully deleted Provider")
