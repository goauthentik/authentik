"""authentik Prompt administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import UpdateView
from guardian.mixins import PermissionRequiredMixin

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
    success_url = reverse_lazy("authentik_core:if-admin")
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
    success_url = reverse_lazy("authentik_core:if-admin")
    success_message = _("Successfully updated Prompt")
