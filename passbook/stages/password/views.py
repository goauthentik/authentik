from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from django.shortcuts import reverse
from django.utils.http import urlencode

from passbook.flows.views import NEXT_ARG_NAME

class UserSettingsCardView(LoginRequiredMixin, TemplateView):

    template_name = "stages/password/user-settings-card.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        base_url = reverse("passbook_flows:configure", kwargs={"stage_uuid": self.kwargs["stage_uuid"]})
        args = urlencode({NEXT_ARG_NAME: reverse("passbook_core:user-settings")})

        kwargs = super().get_context_data(**kwargs)
        kwargs["url"] = f"{base_url}?{args}"
        return kwargs
