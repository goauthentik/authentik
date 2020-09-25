"""passbook Source administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from guardian.mixins import PermissionListMixin, PermissionRequiredMixin

from passbook.admin.views.utils import (
    DeleteMessageView,
    InheritanceCreateView,
    InheritanceListView,
    InheritanceUpdateView, UserPaginateListMixin,
)
from passbook.core.models import Source


class SourceListView(LoginRequiredMixin, PermissionListMixin, UserPaginateListMixin, InheritanceListView):
    """Show list of all sources"""

    model = Source
    permission_required = "passbook_core.view_source"
    ordering = "name"
    template_name = "administration/source/list.html"


class SourceCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    InheritanceCreateView,
):
    """Create new Source"""

    model = Source
    permission_required = "passbook_core.add_source"

    template_name = "generic/create.html"
    success_url = reverse_lazy("passbook_admin:sources")
    success_message = _("Successfully created Source")


class SourceUpdateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    InheritanceUpdateView,
):
    """Update source"""

    model = Source
    permission_required = "passbook_core.change_source"

    template_name = "generic/update.html"
    success_url = reverse_lazy("passbook_admin:sources")
    success_message = _("Successfully updated Source")


class SourceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView):
    """Delete source"""

    model = Source
    permission_required = "passbook_core.delete_source"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("passbook_admin:sources")
    success_message = _("Successfully deleted Source")
