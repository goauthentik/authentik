"""authentik Invitation administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _
from guardian.mixins import PermissionRequiredMixin

from authentik.admin.views.utils import DeleteMessageView
from authentik.lib.views import CreateAssignPermView
from authentik.stages.invitation.forms import InvitationForm
from authentik.stages.invitation.models import Invitation


class InvitationCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new Invitation"""

    model = Invitation
    form_class = InvitationForm
    permission_required = "authentik_stages_invitation.add_invitation"

    template_name = "generic/create.html"
    success_url = "/"
    success_message = _("Successfully created Invitation")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.created_by = self.request.user
        obj.save()
        return HttpResponseRedirect(self.success_url)


class InvitationDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView
):
    """Delete invitation"""

    model = Invitation
    permission_required = "authentik_stages_invitation.delete_invitation"

    template_name = "generic/delete.html"
    success_url = "/"
    success_message = _("Successfully deleted Invitation")
