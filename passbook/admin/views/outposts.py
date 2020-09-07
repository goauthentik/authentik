"""passbook Outpost administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import ListView, UpdateView
from guardian.mixins import PermissionListMixin, PermissionRequiredMixin

from passbook.admin.views.utils import DeleteMessageView
from passbook.lib.views import CreateAssignPermView
from passbook.outposts.forms import OutpostForm
from passbook.outposts.models import Outpost


class OutpostListView(LoginRequiredMixin, PermissionListMixin, ListView):
    """Show list of all outposts"""

    model = Outpost
    permission_required = "passbook_outposts.view_outpost"
    ordering = "name"
    paginate_by = 40
    template_name = "administration/outpost/list.html"


class OutpostCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new Outpost"""

    model = Outpost
    form_class = OutpostForm
    permission_required = "passbook_outposts.add_outpost"

    template_name = "generic/create.html"
    success_url = reverse_lazy("passbook_admin:outposts")
    success_message = _("Successfully created Outpost")


class OutpostUpdateView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """Update outpost"""

    model = Outpost
    form_class = OutpostForm
    permission_required = "passbook_outposts.change_outpost"

    template_name = "generic/update.html"
    success_url = reverse_lazy("passbook_admin:outposts")
    success_message = _("Successfully updated Certificate-Key Pair")


class OutpostDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView):
    """Delete outpost"""

    model = Outpost
    permission_required = "passbook_outposts.delete_outpost"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("passbook_admin:outposts")
    success_message = _("Successfully deleted Certificate-Key Pair")
