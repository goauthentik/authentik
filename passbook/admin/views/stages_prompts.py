"""passbook Prompt administration"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import DeleteView, ListView, UpdateView
from guardian.mixins import PermissionListMixin, PermissionRequiredMixin

from passbook.lib.views import CreateAssignPermView
from passbook.stages.prompt.forms import PromptAdminForm
from passbook.stages.prompt.models import Prompt


class PromptListView(LoginRequiredMixin, PermissionListMixin, ListView):
    """Show list of all prompts"""

    model = Prompt
    permission_required = "passbook_stages_prompt.view_prompt"
    ordering = "field_key"
    paginate_by = 40
    template_name = "administration/stage_prompt/list.html"


class PromptCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new Prompt"""

    model = Prompt
    form_class = PromptAdminForm
    permission_required = "passbook_stages_prompt.add_prompt"

    template_name = "generic/create.html"
    success_url = reverse_lazy("passbook_admin:prompts")
    success_message = _("Successfully created Prompt")

    def get_context_data(self, **kwargs):
        kwargs["type"] = "Prompt"
        return super().get_context_data(**kwargs)


class PromptUpdateView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """Update prompt"""

    model = Prompt
    form_class = PromptAdminForm
    permission_required = "passbook_stages_prompt.change_prompt"

    template_name = "generic/update.html"
    success_url = reverse_lazy("passbook_admin:prompts")
    success_message = _("Successfully updated Prompt")


class PromptDeleteView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    """Delete prompt"""

    model = Prompt
    permission_required = "passbook_stages_prompt.delete_prompt"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("passbook_admin:prompts")
    success_message = _("Successfully deleted Prompt")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)
