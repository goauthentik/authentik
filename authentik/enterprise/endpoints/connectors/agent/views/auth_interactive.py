from datetime import timedelta

from django.http import Http404, HttpRequest, HttpResponse, QueryDict
from django.utils.timezone import now
from jwt import encode

from authentik.crypto.apps import MANAGED_KEY
from authentik.crypto.models import CertificateKeyPair
from authentik.endpoints.connectors.agent.models import AuthenticationToken
from authentik.endpoints.models import Device
from authentik.policies.views import PolicyAccessView
from authentik.providers.oauth2.models import JWTAlgorithms
from authentik.providers.oauth2.utils import HttpResponseRedirectScheme


class AgentInteractiveAuth(PolicyAccessView):

    auth_token: AuthenticationToken
    device: Device

    def resolve_provider_application(self):
        auth_token = (
            AuthenticationToken.objects.filter(identifier=self.kwargs["token_uuid"])
            .prefetch_related()
            .first()
        )
        if not auth_token:
            raise Http404
        self.auth_token = auth_token
        self.device = auth_token.device

    def user_has_access(self, user=None, pbm=None):
        return super().user_has_access(user, self.device)

    def get(self, request: HttpRequest, **kwargs) -> HttpResponse:
        kp = CertificateKeyPair.objects.filter(managed=MANAGED_KEY).first()
        token = encode(
            {
                "iss": "goauthentik.io/platform",
                "aud": str(self.device.pk),
                "jti": str(self.auth_token.identifier),
                "iat": int(now().timestamp()),
                "exp": int((now() + timedelta(days=3)).timestamp()),
                "preferred_username": request.user.username,
            },
            kp.private_key,
            algorithm=JWTAlgorithms.from_private_key(kp.private_key),
        )
        qd = QueryDict(mutable=True)
        qd["ak-auth-ia-token"] = token
        self.auth_token.token = token
        self.auth_token.save()
        return HttpResponseRedirectScheme(
            "goauthentik.io://platform/finished" + "?" + qd.urlencode(),
            allowed_schemes=["goauthentik.io"],
        )
