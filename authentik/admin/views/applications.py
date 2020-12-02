"""authentik Application administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import ListView, UpdateView
from guardian.mixins import PermissionListMixin, PermissionRequiredMixin

from authentik.admin.views.utils import (
    BackSuccessUrlMixin,
    DeleteMessageView,
    SearchListMixin,
    UserPaginateListMixin,
)
from authentik.core.forms.applications import ApplicationForm
from authentik.core.models import Application
from authentik.lib.views import CreateAssignPermView


class ApplicationListView(
    LoginRequiredMixin,
    PermissionListMixin,
    UserPaginateListMixin,
    SearchListMixin,
    ListView,
):
    """Show list of all applications"""

    model = Application
    permission_required = "authentik_core.view_application"
    ordering = "name"
    template_name = "administration/application/list.html"

    search_fields = [
        "name",
        "slug",
        "meta_launch_url",
        "meta_icon_url",
        "meta_description",
        "meta_publisher",
    ]


class ApplicationCreateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new Application"""

    model = Application
    form_class = ApplicationForm
    permission_required = "authentik_core.add_application"

    template_name = "generic/create.html"
    success_url = reverse_lazy("authentik_admin:applications")
    success_message = _("Successfully created Application")


class ApplicationUpdateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    """Update application"""

    model = Application
    form_class = ApplicationForm
    permission_required = "authentik_core.change_application"

    template_name = "generic/update.html"
    success_url = reverse_lazy("authentik_admin:applications")
    success_message = _("Successfully updated Application")


class ApplicationDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView
):
    """Delete application"""

    model = Application
    permission_required = "authentik_core.delete_application"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("authentik_admin:applications")
    success_message = _("Successfully deleted Application")
