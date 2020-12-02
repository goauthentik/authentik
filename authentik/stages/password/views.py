"""password stage user settings card"""
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import reverse
from django.utils.http import urlencode
from django.views.generic import TemplateView

from authentik.flows.views import NEXT_ARG_NAME


class UserSettingsCardView(LoginRequiredMixin, TemplateView):
    """Card shown on user settings page to allow user to change their password"""

    template_name = "stages/password/user-settings-card.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        base_url = reverse(
            "authentik_flows:configure",
            kwargs={"stage_uuid": self.kwargs["stage_uuid"]},
        )
        args = urlencode({NEXT_ARG_NAME: reverse("authentik_core:user-settings")})

        kwargs = super().get_context_data(**kwargs)
        kwargs["url"] = f"{base_url}?{args}"
        return kwargs
