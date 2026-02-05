from dataclasses import dataclass

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

    @staticmethod
    def parse(request: HttpRequest) -> SignOutRequest:
        action = request.GET.get("wa")
        if action != WS_FED_ACTION_SIGN_OUT:
            raise ValueError("Invalid action")
        realm = request.GET.get("wtrealm")
        if not realm:
            raise ValueError("Missing Realm")

        req = SignOutRequest(
            wa=action,
            wtrealm=realm,
            wreply=request.GET.get("wreply"),
        )

        _, provider = req.get_app_provider()
        if not req.wreply:
            req.wreply = provider.acs_url
        if not req.wreply.startswith(provider.acs_url):
            raise ValueError("Invalid wreply")
        return req

    def get_app_provider(self):
        provider: WSFederationProvider = get_object_or_404(
            WSFederationProvider, audience=self.wtrealm
        )
        application = get_object_or_404(Application, provider=provider)
        return application, provider
