"""authentik OAuth2 Session Views"""
from typing import Any, Dict

from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView

from authentik.core.models import Application


class EndSessionView(TemplateView):
    """Allow the client to end the Session"""

    template_name = "providers/oauth2/end_session.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["application"] = get_object_or_404(
            Application, slug=self.kwargs["application_slug"]
        )

        return context
