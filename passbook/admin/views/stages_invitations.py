"""passbook Invitation administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import ListView
from guardian.mixins import PermissionListMixin, PermissionRequiredMixin

from passbook.admin.views.utils import DeleteMessageView
from passbook.lib.views import CreateAssignPermView
from passbook.stages.invitation.forms import InvitationForm
from passbook.stages.invitation.models import Invitation
from passbook.stages.invitation.signals import invitation_created


class InvitationListView(LoginRequiredMixin, PermissionListMixin, ListView):
    """Show list of all invitations"""

    model = Invitation
    permission_required = "passbook_stages_invitation.view_invitation"
    template_name = "administration/stage_invitation/list.html"
    paginate_by = 10
    ordering = "-expires"


class InvitationCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new Invitation"""

    model = Invitation
    form_class = InvitationForm
    permission_required = "passbook_stages_invitation.add_invitation"

    template_name = "generic/create.html"
    success_url = reverse_lazy("passbook_admin:stage-invitations")
    success_message = _("Successfully created Invitation")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.created_by = self.request.user
        obj.save()
        invitation_created.send(sender=self, request=self.request, invitation=obj)
        return HttpResponseRedirect(self.success_url)


class InvitationDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView
):
    """Delete invitation"""

    model = Invitation
    permission_required = "passbook_stages_invitation.delete_invitation"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("passbook_admin:stage-invitations")
    success_message = _("Successfully deleted Invitation")
