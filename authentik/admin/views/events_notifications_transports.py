"""authentik NotificationTransport administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import gettext as _
from django.views.generic import UpdateView
from guardian.mixins import PermissionRequiredMixin

from authentik.events.forms import NotificationTransportForm
from authentik.events.models import NotificationTransport
from authentik.lib.views import CreateAssignPermView


class NotificationTransportCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new NotificationTransport"""

    model = NotificationTransport
    form_class = NotificationTransportForm
    permission_required = "authentik_events.add_notificationtransport"
    success_url = "/"
    template_name = "generic/create.html"
    success_message = _("Successfully created Notification Transport")


class NotificationTransportUpdateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    """Update application"""

    model = NotificationTransport
    form_class = NotificationTransportForm
    permission_required = "authentik_events.change_notificationtransport"
    success_url = "/"
    template_name = "generic/update.html"
    success_message = _("Successfully updated Notification Transport")
