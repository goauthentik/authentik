"""authentik Application administration"""
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import gettext as _
from django.views.generic import UpdateView
from guardian.mixins import PermissionRequiredMixin
from guardian.shortcuts import get_objects_for_user

from authentik.admin.views.utils import DeleteMessageView
from authentik.core.forms.applications import ApplicationForm
from authentik.core.models import Application
from authentik.lib.views import CreateAssignPermView


class ApplicationCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new Application"""

    model = Application
    form_class = ApplicationForm
    permission_required = "authentik_core.add_application"

    template_name = "generic/create.html"
    success_message = _("Successfully created Application")

    def get_initial(self) -> dict[str, Any]:
        if "provider" in self.request.GET:
            try:
                initial_provider_pk = int(self.request.GET["provider"])
            except ValueError:
                return super().get_initial()
            providers = (
                get_objects_for_user(self.request.user, "authentik_core.view_provider")
                .filter(pk=initial_provider_pk)
                .select_subclasses()
            )
            if not providers.exists():
                return {}
            return {"provider": providers.first()}
        return super().get_initial()


class ApplicationUpdateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    """Update application"""

    model = Application
    form_class = ApplicationForm
    permission_required = "authentik_core.change_application"

    template_name = "generic/update.html"
    success_message = _("Successfully updated Application")


class ApplicationDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView
):
    """Delete application"""

    model = Application
    permission_required = "authentik_core.delete_application"

    template_name = "generic/delete.html"
    success_message = _("Successfully deleted Application")
