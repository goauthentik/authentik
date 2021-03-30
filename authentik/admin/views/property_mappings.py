"""authentik PropertyMapping administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import gettext as _
from guardian.mixins import PermissionRequiredMixin

from authentik.admin.views.utils import InheritanceCreateView, InheritanceUpdateView
from authentik.core.models import PropertyMapping


class PropertyMappingCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    InheritanceCreateView,
):
    """Create new PropertyMapping"""

    model = PropertyMapping
    permission_required = "authentik_core.add_propertymapping"
    success_url = "/"
    template_name = "generic/create.html"
    success_message = _("Successfully created Property Mapping")


class PropertyMappingUpdateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    InheritanceUpdateView,
):
    """Update property_mapping"""

    model = PropertyMapping
    permission_required = "authentik_core.change_propertymapping"
    success_url = "/"
    template_name = "generic/update.html"
    success_message = _("Successfully updated Property Mapping")
