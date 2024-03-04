"""General API Views"""

from typing import Any

from django.urls import reverse
from django.views.generic import TemplateView


class APIBrowserView(TemplateView):
    """Show browser view based on rapi-doc"""

    template_name = "api/browser.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        path = self.request.build_absolute_uri(
            reverse(
                "authentik_api:schema",
            )
        )
        return super().get_context_data(path=path, **kwargs)
