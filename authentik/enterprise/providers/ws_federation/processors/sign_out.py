from dataclasses import dataclass
from urllib.parse import urlparse

from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from authentik.core.models import Application
from authentik.enterprise.providers.ws_federation.models import WSFederationProvider
from authentik.enterprise.providers.ws_federation.processors.constants import WS_FED_ACTION_SIGN_OUT


@dataclass()
class SignOutRequest:
    wa: str
    wtrealm: str
    wreply: str

    app_slug: str

    @staticmethod
    def parse(request: HttpRequest) -> SignOutRequest:
        action = request.GET.get("wa")
        if action != WS_FED_ACTION_SIGN_OUT:
            raise ValueError("Invalid action")
        realm = request.GET.get("wtrealm")
        if not realm:
            raise ValueError("Missing Realm")
        parsed = urlparse(realm)

        req = SignOutRequest(
            wa=action,
            wtrealm=realm,
            wreply=request.GET.get("wreply"),
            app_slug=parsed.path[1:],
        )

        _, provider = req.get_app_provider()
        if not req.wreply.startswith(provider.acs_url):
            raise ValueError("Invalid wreply")
        return req

    def get_app_provider(self):
        application = get_object_or_404(Application, slug=self.app_slug)
        provider: WSFederationProvider = get_object_or_404(
            WSFederationProvider, pk=application.provider_id
        )
        return application, provider
