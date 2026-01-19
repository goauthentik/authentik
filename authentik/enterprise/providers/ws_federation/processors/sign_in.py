from base64 import b64encode
from dataclasses import dataclass
from uuid import uuid4

from django.http import HttpRequest

from authentik.enterprise.providers.ws_federation.models import WSFederationProvider
from authentik.enterprise.providers.ws_federation.processors.constants import (
    WS_FED_ACTION_SIGN_IN,
    WS_FED_POST_KEY_ACTION,
    WS_FED_POST_KEY_CONTEXT,
    WS_FED_POST_KEY_RESULT,
)
from authentik.policies.utils import delete_none_values
from authentik.providers.saml.processors.assertion import AssertionProcessor
from authentik.providers.saml.processors.authn_request_parser import AuthNRequest


@dataclass()
class SignInRequest:
    wa: str
    wtrealm: str
    wreply: str
    http_request: HttpRequest
    wctx: str | None


class SignInProcessor:
    def __init__(self, provider: WSFederationProvider):
        self.provider = provider

    def parse(self, request: HttpRequest) -> SignInRequest:
        return SignInRequest(
            wa=request.GET.get("wa"),
            wtrealm=request.GET.get("wtrealm"),
            wreply=request.GET.get("wreply"),
            wctx=request.GET.get("wctx", ""),
            http_request=request,
        )

    def response(self, request: SignInRequest) -> dict:
        req = AuthNRequest(uuid4())
        proc = AssertionProcessor(self.provider, request.http_request, req)
        saml_token = proc.build_response()
        encoded_token = b64encode(saml_token.encode("utf-8")).decode("utf-8")
        return delete_none_values(
            {
                WS_FED_POST_KEY_ACTION: WS_FED_ACTION_SIGN_IN,
                WS_FED_POST_KEY_RESULT: encoded_token,
                WS_FED_POST_KEY_CONTEXT: request.wctx,
            }
        )
