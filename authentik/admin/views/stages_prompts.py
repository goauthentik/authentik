"""authentik Prompt administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import gettext as _
from django.views.generic import UpdateView
from guardian.mixins import PermissionRequiredMixin

from authentik.admin.views.utils import DeleteMessageView
from authentik.lib.views import CreateAssignPermView
from authentik.stages.prompt.forms import PromptAdminForm
from authentik.stages.prompt.models import Prompt


class PromptCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new Prompt"""

    model = Prompt
    form_class = PromptAdminForm
    permission_required = "authentik_stages_prompt.add_prompt"

    template_name = "generic/create.html"
    success_url = "/"
    success_message = _("Successfully created Prompt")


class PromptUpdateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    """Update prompt"""

    model = Prompt
    form_class = PromptAdminForm
    permission_required = "authentik_stages_prompt.change_prompt"

    template_name = "generic/update.html"
    success_url = "/"
    success_message = _("Successfully updated Prompt")


class PromptDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView):
    """Delete prompt"""

    model = Prompt
    permission_required = "authentik_stages_prompt.delete_prompt"

    template_name = "generic/delete.html"
    success_url = "/"
    success_message = _("Successfully deleted Prompt")
