from dataclasses import InitVar, dataclass
from urllib.parse import urlparse

from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from authentik.core.models import Application
from authentik.enterprise.providers.ws_federation.models import WSFederationProvider
from authentik.enterprise.providers.ws_federation.processors.constants import (
    WS_FED_ACTION_SIGN_OUT,
    WS_FED_QS_ACTION,
    WS_FED_QS_REALM,
    WS_FED_QS_REPLY,
)


@dataclass()
class SignOutRequest:
    wa: str
    wtrealm: str
    wreply: str
    request: InitVar[HttpRequest]

    @staticmethod
    def parse(request: HttpRequest) -> SignOutRequest:
        return SignOutRequest(
            wa=request.GET.get(WS_FED_QS_ACTION),
            wtrealm=request.GET.get(WS_FED_QS_REALM),
            wreply=request.GET.get(WS_FED_QS_REPLY),
            request=request,
        )

    def __post_init__(self, request: HttpRequest):
        if self.wa != WS_FED_ACTION_SIGN_OUT:
            raise ValueError("Invalid action")
        self.__post_init_resolve_realm(request)
        _, provider = self.get_app_provider()
        if not self.wreply:
            self.wreply = provider.acs_url
        if not self.wtrealm:
            raise ValueError("Missing Realm")
        reply = urlparse(self.wreply)
        configured = urlparse(provider.acs_url)
        if not (reply[:2] == configured[:2] and reply.path.startswith(configured.path)):
            raise ValueError("Invalid wreply")

    def __post_init_resolve_realm(self, request: HttpRequest):
        slug = request.resolver_match.kwargs.get("application_slug")
        if not slug:
            return
        app = get_object_or_404(Application, slug=slug)
        provider = get_object_or_404(WSFederationProvider, pk=app.provider_id)
        self.wtrealm = provider.audience

    def get_app_provider(self):
        provider: WSFederationProvider = get_object_or_404(
            WSFederationProvider, audience=self.wtrealm
        )
        application = get_object_or_404(Application, provider=provider)
        return application, provider
