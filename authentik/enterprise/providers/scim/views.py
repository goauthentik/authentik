from datetime import timedelta

from django.http import HttpRequest, HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.timezone import now

from authentik.core.models import Application
from authentik.providers.scim.models import SCIMProvider
from authentik.sources.oauth.clients.base import BaseOAuthClient
from authentik.sources.oauth.models import OAuthSource, UserOAuthSourceConnection
from authentik.sources.oauth.types.registry import RequestKind, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect


def get_scim_provider(app_slug: str):
    app = Application.objects.filter(slug=app_slug).first()
    if not app:
        return None
    provider = SCIMProvider.objects.filter(backchannel_application=app)
    return provider.first()


class SCIMOAuthViewMixin:
    provider: SCIMProvider

    def get_client(self, source: OAuthSource, **kwargs) -> BaseOAuthClient:
        source: OAuthSource = self.provider.auth_oauth
        source_cls = registry.find(source.provider_type, kind=RequestKind.CALLBACK)
        if not source_cls.client_class:
            return super().get_client(source, **kwargs)
        return source_cls.client_class(source, self.request, **kwargs)

    def dispatch(self, request: HttpRequest, application_slug: str):
        provider = get_scim_provider(application_slug)
        if not provider or not provider.auth_oauth:
            return HttpResponseBadRequest()
        self.provider = provider
        return super().dispatch(request, source_slug=provider.auth_oauth.slug)


class SCIMOAuthStart(SCIMOAuthViewMixin, OAuthRedirect):

    def get_callback_url(self, source: OAuthSource):
        return reverse("authentik_enterprise_providers_scim:callback", kwargs=self.kwargs)


class SCIMRedirectCallback(SCIMOAuthViewMixin, OAuthCallback):

    def redirect_flow_manager(self, client: BaseOAuthClient):
        expires_in = int(self.token.get("expires_in", 0))
        UserOAuthSourceConnection.objects.update_or_create(
            source=self.provider.auth_oauth,
            user=self.provider.auth_oauth_user,
            defaults={
                "access_token": self.token.get("access_token"),
                "refresh_token": self.token.get("refresh_token"),
                "expires": now() + timedelta(seconds=expires_in),
            },
        )
        return redirect("authentik_core:if-admin")
