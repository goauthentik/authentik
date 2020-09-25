"""passbook Prompt administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import ListView, UpdateView
from guardian.mixins import PermissionListMixin, PermissionRequiredMixin

from passbook.admin.views.utils import (
    BackSuccessUrlMixin,
    DeleteMessageView,
    UserPaginateListMixin,
)
from passbook.lib.views import CreateAssignPermView
from passbook.stages.prompt.forms import PromptAdminForm
from passbook.stages.prompt.models import Prompt


class PromptListView(
    LoginRequiredMixin, PermissionListMixin, UserPaginateListMixin, ListView
):
    """Show list of all prompts"""

    model = Prompt
    permission_required = "passbook_stages_prompt.view_prompt"
    ordering = "order"
    template_name = "administration/stage_prompt/list.html"


class PromptCreateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new Prompt"""

    model = Prompt
    form_class = PromptAdminForm
    permission_required = "passbook_stages_prompt.add_prompt"

    template_name = "generic/create.html"
    success_url = reverse_lazy("passbook_admin:stage-prompts")
    success_message = _("Successfully created Prompt")


class PromptUpdateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    """Update prompt"""

    model = Prompt
    form_class = PromptAdminForm
    permission_required = "passbook_stages_prompt.change_prompt"

    template_name = "generic/update.html"
    success_url = reverse_lazy("passbook_admin:stage-prompts")
    success_message = _("Successfully updated Prompt")


class PromptDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView):
    """Delete prompt"""

    model = Prompt
    permission_required = "passbook_stages_prompt.delete_prompt"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("passbook_admin:stage-prompts")
    success_message = _("Successfully deleted Prompt")
