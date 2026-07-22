from dataclasses import dataclass
from urllib.parse import urlparse

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from lxml import etree  # nosec
from lxml.etree import Element, SubElement, _Element  # nosec

from authentik.core.models import Application
from authentik.enterprise.providers.ws_federation.models import (
    WSFederationProvider,
    WSFederationSAMLVersion,
)
from authentik.enterprise.providers.ws_federation.processors.assertion_saml11 import (
    SAML11AssertionProcessor,
)
from authentik.enterprise.providers.ws_federation.processors.constants import (
    NS_ADDRESSING,
    NS_MAP,
    NS_POLICY,
    NS_WS_FED_TRUST,
    NS_WSS_D3P1,
    NS_WSS_SEC,
    NS_WSS_UTILITY,
    WS_FED_ACTION_SIGN_IN,
    WS_FED_POST_KEY_ACTION,
    WS_FED_POST_KEY_CONTEXT,
    WS_FED_POST_KEY_RESULT,
    WS_FED_QS_ACTION,
    WS_FED_QS_REALM,
    WS_FED_QS_REPLY,
    WSS_KEY_IDENTIFIER_SAML_ID,
    WSS_TOKEN_TYPE_BY_VERSION,
)
from authentik.lib.utils.time import timedelta_from_string
from authentik.policies.utils import delete_none_values
from authentik.providers.saml.processors.assertion import AssertionProcessor
from authentik.providers.saml.processors.authn_request_parser import AuthNRequest
from authentik.providers.saml.utils.time import get_time_string


@dataclass()
class SignInRequest:
    wa: str
    wtrealm: str
    wreply: str
    wctx: str | None

    @staticmethod
    def parse(request: HttpRequest) -> SignInRequest:
        req = SignInRequest(
            wa=request.GET.get(WS_FED_QS_ACTION),
            wtrealm=request.GET.get(WS_FED_QS_REALM),
            wreply=request.GET.get(WS_FED_QS_REPLY),
            wctx=request.GET.get(WS_FED_POST_KEY_CONTEXT, ""),
        )
        return req

    def __post_init__(self):
        if self.action != WS_FED_ACTION_SIGN_IN:
            raise ValueError("Invalid action")
        if not self.realm:
            raise ValueError("Missing Realm")
        _, provider = self.get_app_provider()
        if not self.wreply:
            self.wreply = provider.acs_url
        reply = urlparse(self.wreply)
        configured = urlparse(provider.acs_url)
        if not (reply[:2] == configured[:2] and reply.path.startswith(configured.path)):
            raise ValueError("Invalid wreply")

    def get_app_provider(self):
        provider: WSFederationProvider = get_object_or_404(
            WSFederationProvider, audience=self.wtrealm
        )
        application = get_object_or_404(Application, provider=provider)
        return application, provider


class SignInProcessor:
    provider: WSFederationProvider
    request: HttpRequest
    sign_in_request: SignInRequest
    saml_processor: AssertionProcessor

    def __init__(
        self, provider: WSFederationProvider, request: HttpRequest, sign_in_request: SignInRequest
    ):
        self.provider = provider
        self.request = request
        self.sign_in_request = sign_in_request
        processor_cls = (
            SAML11AssertionProcessor
            if self.provider.saml_version == WSFederationSAMLVersion.SAML_1_1
            else AssertionProcessor
        )
        self.saml_processor = processor_cls(self.provider, self.request, AuthNRequest())
        self.saml_processor.provider.audience = self.sign_in_request.wtrealm
        if self.provider.signing_kp:
            self.saml_processor.provider.sign_assertion = True

    def create_response_token(self):
        root = Element(f"{{{NS_WS_FED_TRUST}}}RequestSecurityTokenResponse", nsmap=NS_MAP)

        root.append(self.response_add_lifetime())
        root.append(self.response_add_applies_to())
        root.append(self.response_add_requested_security_token())
        root.append(
            self.response_add_attached_reference(
                "RequestedAttachedReference", self.saml_processor._assertion_id
            )
        )
        root.append(
            self.response_add_attached_reference(
                "RequestedUnattachedReference", self.saml_processor._assertion_id
            )
        )

        token_type = SubElement(root, f"{{{NS_WS_FED_TRUST}}}TokenType")
        token_type.text = WSS_TOKEN_TYPE_BY_VERSION[self.provider.saml_version]

        request_type = SubElement(root, f"{{{NS_WS_FED_TRUST}}}RequestType")
        request_type.text = "http://schemas.xmlsoap.org/ws/2005/02/trust/Issue"

        key_type = SubElement(root, f"{{{NS_WS_FED_TRUST}}}KeyType")
        key_type.text = "http://schemas.xmlsoap.org/ws/2005/05/identity/NoProofKey"

        return root

    def response_add_lifetime(self) -> _Element:
        """Add Lifetime element"""
        lifetime = Element(f"{{{NS_WS_FED_TRUST}}}Lifetime", nsmap=NS_MAP)
        created = SubElement(lifetime, f"{{{NS_WSS_UTILITY}}}Created")
        created.text = get_time_string()
        expires = SubElement(lifetime, f"{{{NS_WSS_UTILITY}}}Expires")
        expires.text = get_time_string(
            timedelta_from_string(self.provider.session_valid_not_on_or_after)
        )
        return lifetime

    def response_add_applies_to(self) -> _Element:
        """Add AppliesTo element"""
        applies_to = Element(f"{{{NS_POLICY}}}AppliesTo")
        endpoint_ref = SubElement(applies_to, f"{{{NS_ADDRESSING}}}EndpointReference")
        address = SubElement(endpoint_ref, f"{{{NS_ADDRESSING}}}Address")
        address.text = self.sign_in_request.wtrealm
        return applies_to

    def response_add_requested_security_token(self) -> _Element:
        """Add RequestedSecurityToken and child assertion"""
        token = Element(f"{{{NS_WS_FED_TRUST}}}RequestedSecurityToken")
        token.append(self.saml_processor.get_assertion())
        return token

    def response_add_attached_reference(self, tag: str, value: str) -> _Element:
        ref = Element(f"{{{NS_WS_FED_TRUST}}}{tag}")
        sec_token_ref = SubElement(ref, f"{{{NS_WSS_SEC}}}SecurityTokenReference")
        sec_token_ref.attrib[f"{{{NS_WSS_D3P1}}}TokenType"] = WSS_TOKEN_TYPE_BY_VERSION[
            self.provider.saml_version
        ]

        key_identifier = SubElement(sec_token_ref, f"{{{NS_WSS_SEC}}}KeyIdentifier")
        key_identifier.attrib["ValueType"] = WSS_KEY_IDENTIFIER_SAML_ID
        key_identifier.text = value
        return ref

    def response(self) -> dict[str, str]:
        root = self.create_response_token()
        # match by local name, since "saml" may be bound to the 1.1 or 2.0 namespace here
        assertion = root.xpath("//*[local-name()='Assertion']")[0]
        if self.provider.signing_kp:
            self.saml_processor._sign(assertion)
        str_token = etree.tostring(root).decode("utf-8")  # nosec
        return delete_none_values(
            {
                WS_FED_POST_KEY_ACTION: WS_FED_ACTION_SIGN_IN,
                WS_FED_POST_KEY_RESULT: str_token,
                WS_FED_POST_KEY_CONTEXT: self.sign_in_request.wctx,
            }
        )
