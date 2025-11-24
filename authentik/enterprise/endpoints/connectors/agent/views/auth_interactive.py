from django.http import Http404, HttpRequest, HttpResponse, QueryDict
from django.utils.timezone import now
from jwt import encode

from authentik.crypto.apps import MANAGED_KEY
from authentik.crypto.models import CertificateKeyPair
from authentik.endpoints.connectors.agent.models import AuthenticationToken
from authentik.lib.utils.urls import redirect_with_qs
from authentik.policies.views import PolicyAccessView
from authentik.providers.oauth2.models import JWTAlgorithms


class AgentInteractiveAuth(PolicyAccessView):

    def resolve_provider_application(self):
        auth_token = AuthenticationToken.objects.filter(
            identifier=self.kwargs["token_uuid"]
        ).prefetch_related().first()
        if not auth_token:
            raise Http404
        self.auth_token = auth_token
        self.application = auth_token.device

    def get(self, request: HttpRequest) -> HttpResponse:
        kp = CertificateKeyPair.objects.filter(managed=MANAGED_KEY).first()
        token = encode({
            "iss": "goauthentik.io/platform",
            "aud": self.application.pk,
            "iat": int(now().timestamp()),
        }, kp.private_key, algorithm=JWTAlgorithms.from_private_key(kp.private_key))
        qd = QueryDict(mutable=True)
        qd["ak-auth-ia-token"] = token
        return redirect_with_qs("goauthentik.io://platform/finished", qd)
