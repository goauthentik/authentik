"""OAuth Redirect Views"""
from typing import Any

from django.http import Http404
from django.urls import reverse
from django.views.generic import RedirectView
from structlog.stdlib import get_logger

from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.views.base import OAuthClientMixin

LOGGER = get_logger()


class OAuthRedirect(OAuthClientMixin, RedirectView):
    "Redirect user to OAuth source to enable access."

    permanent = False
    params = None

    def get_additional_parameters(self, source: OAuthSource) -> dict[str, Any]:
        "Return additional redirect parameters for this source."
        return self.params or {}

    def get_callback_url(self, source: OAuthSource) -> str:
        "Return the callback url for this source."
        return reverse(
            "authentik_sources_oauth:oauth-client-callback",
            kwargs={"source_slug": source.slug},
        )

    def get_redirect_url(self, **kwargs) -> str:
        "Build redirect url for a given source."
        slug = kwargs.get("source_slug", "")
        try:
            source: OAuthSource = OAuthSource.objects.get(slug=slug)
        except OAuthSource.DoesNotExist:
            raise Http404(f"Unknown OAuth source '{slug}'.")
        else:
            if not source.enabled:
                raise Http404(f"source {slug} is not enabled.")
            client = self.get_client(source, callback=self.get_callback_url(source))
            params = self.get_additional_parameters(source)
            params.setdefault("scope", [])
            if source.additional_scopes != "":
                if source.additional_scopes.startswith("*"):
                    params["scope"] = source.additional_scopes[1:].split(" ")
                else:
                    params["scope"] += source.additional_scopes.split(" ")
            return client.get_redirect_url(params)
