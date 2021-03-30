"""authentik Policy administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from guardian.mixins import PermissionRequiredMixin

from authentik.admin.views.utils import InheritanceCreateView, InheritanceUpdateView
from authentik.policies.models import Policy


class PolicyCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    InheritanceCreateView,
):
    """Create new Policy"""

    model = Policy
    permission_required = "authentik_policies.add_policy"

    template_name = "generic/create.html"
    success_url = reverse_lazy("authentik_core:if-admin")
    success_message = _("Successfully created Policy")


class PolicyUpdateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    InheritanceUpdateView,
):
    """Update policy"""

    model = Policy
    permission_required = "authentik_policies.change_policy"

    template_name = "generic/update.html"
    success_url = reverse_lazy("authentik_core:if-admin")
    success_message = _("Successfully updated Policy")
