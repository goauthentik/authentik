"""authentik NotificationRule administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import gettext as _
from django.views.generic import UpdateView
from guardian.mixins import PermissionRequiredMixin

from authentik.admin.views.utils import DeleteMessageView
from authentik.events.forms import NotificationRuleForm
from authentik.events.models import NotificationRule
from authentik.lib.views import CreateAssignPermView


class NotificationRuleCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new NotificationRule"""

    model = NotificationRule
    form_class = NotificationRuleForm
    permission_required = "authentik_events.add_NotificationRule"

    template_name = "generic/create.html"
    success_message = _("Successfully created Notification Rule")


class NotificationRuleUpdateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    """Update application"""

    model = NotificationRule
    form_class = NotificationRuleForm
    permission_required = "authentik_events.change_NotificationRule"

    template_name = "generic/update.html"
    success_message = _("Successfully updated Notification Rule")


class NotificationRuleDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView
):
    """Delete application"""

    model = NotificationRule
    permission_required = "authentik_events.delete_NotificationRule"

    template_name = "generic/delete.html"
    success_message = _("Successfully deleted Notification Rule")
