"""authentik NotificationTransport administration"""
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
from authentik.events.forms import NotificationTransportForm
from authentik.events.models import NotificationTransport
from authentik.lib.views import CreateAssignPermView


class NotificationTransportCreateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new NotificationTransport"""

    model = NotificationTransport
    form_class = NotificationTransportForm
    permission_required = "authentik_events.add_notificationtransport"

    template_name = "generic/create.html"
    success_url = reverse_lazy("authentik_core:shell")
    success_message = _("Successfully created Notification Transport")


class NotificationTransportUpdateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    """Update application"""

    model = NotificationTransport
    form_class = NotificationTransportForm
    permission_required = "authentik_events.change_notificationtransport"

    template_name = "generic/update.html"
    success_url = reverse_lazy("authentik_core:shell")
    success_message = _("Successfully updated Notification Transport")


class NotificationTransportDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView
):
    """Delete application"""

    model = NotificationTransport
    permission_required = "authentik_events.delete_notificationtransport"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("authentik_core:shell")
    success_message = _("Successfully deleted Notification Transport")
