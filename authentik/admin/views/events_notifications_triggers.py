"""authentik NotificationTrigger administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import UpdateView
from guardian.mixins import PermissionRequiredMixin

from authentik.admin.views.utils import BackSuccessUrlMixin, DeleteMessageView
from authentik.events.forms import NotificationTriggerForm
from authentik.events.models import NotificationTrigger
from authentik.lib.views import CreateAssignPermView


class NotificationTriggerCreateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new NotificationTrigger"""

    model = NotificationTrigger
    form_class = NotificationTriggerForm
    permission_required = "authentik_events.add_notificationtrigger"

    template_name = "generic/create.html"
    success_url = reverse_lazy("authentik_core:shell")
    success_message = _("Successfully created Notification Trigger")


class NotificationTriggerUpdateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    """Update application"""

    model = NotificationTrigger
    form_class = NotificationTriggerForm
    permission_required = "authentik_events.change_notificationtrigger"

    template_name = "generic/update.html"
    success_url = reverse_lazy("authentik_core:shell")
    success_message = _("Successfully updated Notification Trigger")


class NotificationTriggerDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView
):
    """Delete application"""

    model = NotificationTrigger
    permission_required = "authentik_events.delete_notificationtrigger"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("authentik_core:shell")
    success_message = _("Successfully deleted Notification Trigger")
