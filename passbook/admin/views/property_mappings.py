"""passbook PropertyMapping administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from guardian.mixins import PermissionListMixin, PermissionRequiredMixin

from passbook.admin.views.utils import (
    BackSuccessUrlMixin,
    DeleteMessageView,
    InheritanceCreateView,
    InheritanceListView,
    InheritanceUpdateView,
    SearchListMixin,
    UserPaginateListMixin,
)
from passbook.core.models import PropertyMapping


class PropertyMappingListView(
    LoginRequiredMixin,
    PermissionListMixin,
    UserPaginateListMixin,
    SearchListMixin,
    InheritanceListView,
):
    """Show list of all property_mappings"""

    model = PropertyMapping
    permission_required = "passbook_core.view_propertymapping"
    template_name = "administration/property_mapping/list.html"
    ordering = "name"
    search_fields = ["name", "expression"]


class PropertyMappingCreateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    InheritanceCreateView,
):
    """Create new PropertyMapping"""

    model = PropertyMapping
    permission_required = "passbook_core.add_propertymapping"

    template_name = "generic/create.html"
    success_url = reverse_lazy("passbook_admin:property-mappings")
    success_message = _("Successfully created Property Mapping")


class PropertyMappingUpdateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    InheritanceUpdateView,
):
    """Update property_mapping"""

    model = PropertyMapping
    permission_required = "passbook_core.change_propertymapping"

    template_name = "generic/update.html"
    success_url = reverse_lazy("passbook_admin:property-mappings")
    success_message = _("Successfully updated Property Mapping")


class PropertyMappingDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView
):
    """Delete property_mapping"""

    model = PropertyMapping
    permission_required = "passbook_core.delete_propertymapping"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("passbook_admin:property-mappings")
    success_message = _("Successfully deleted Property Mapping")
