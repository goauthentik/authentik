"""authentik Session Views"""
from typing import Any

from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView

from authentik.core.models import Application
from authentik.policies.views import PolicyAccessView


class EndSessionView(TemplateView, PolicyAccessView):
    """Allow the client to end the Session"""

    template_name = "if/end_session.html"

    def resolve_provider_application(self):
        self.application = get_object_or_404(
            Application, tenant=self.request.tenant, slug=self.kwargs["application_slug"]
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["application"] = self.application
        return context
