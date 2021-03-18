"""authentik Group administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import UpdateView
from guardian.mixins import PermissionRequiredMixin

from authentik.core.forms.groups import GroupForm
from authentik.core.models import Group
from authentik.lib.views import CreateAssignPermView


class GroupCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new Group"""

    model = Group
    form_class = GroupForm
    permission_required = "authentik_core.add_group"

    template_name = "generic/create.html"
    success_url = reverse_lazy("authentik_core:shell")
    success_message = _("Successfully created Group")


class GroupUpdateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    """Update group"""

    model = Group
    form_class = GroupForm
    permission_required = "authentik_core.change_group"

    template_name = "generic/update.html"
    success_url = reverse_lazy("authentik_core:shell")
    success_message = _("Successfully updated Group")
