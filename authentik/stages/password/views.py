"""password stage user settings card"""
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from authentik.stages.password.models import PasswordStage


class UserSettingsCardView(LoginRequiredMixin, TemplateView):
    """Card shown on user settings page to allow user to change their password"""

    template_name = "stages/password/user-settings-card.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        stage = get_object_or_404(PasswordStage, pk=self.kwargs["stage_uuid"])
        kwargs = super().get_context_data(**kwargs)
        kwargs["stage"] = stage
        return kwargs
