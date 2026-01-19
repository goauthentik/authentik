from dataclasses import dataclass
from urllib.parse import urlparse

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from lxml import etree  # nosec
from lxml.etree import Element, SubElement  # nosec

from authentik.core.models import Application
from authentik.enterprise.providers.ws_federation.models import WSFederationProvider
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
    WSS_KEY_IDENTIFIER_SAML_ID,
    WSS_TOKEN_TYPE_SAML2,
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

    app_slug: str

    @staticmethod
    def parse(request: HttpRequest) -> SignInRequest:
        action = request.GET.get("wa")
        if action != WS_FED_ACTION_SIGN_IN:
            raise ValueError("Invalid action")
        realm = request.GET.get("wtrealm")
        if not realm:
            raise ValueError("Missing Realm")
        parsed = urlparse(realm)

        req = SignInRequest(
            wa=action,
            wtrealm=realm,
            wreply=request.GET.get("wreply"),
            wctx=request.GET.get("wctx", ""),
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


class SignInProcessor:
    def __init__(
        self, provider: WSFederationProvider, request: HttpRequest, sign_in_request: SignInRequest
    ):
        self.provider = provider
        self.request = request
        self.sign_in_request = sign_in_request

    def create_response_token(self):
        root = Element(f"{{{NS_WS_FED_TRUST}}}RequestSecurityTokenResponse", nsmap=NS_MAP)

        self.response_add_lifetime(root)
        self.response_add_applies_to(root)
        assertion_proc = self.response_add_requested_security_token(root)
        self.response_add_attached_reference(
            root, "RequestedAttachedReference", assertion_proc._assertion_id
        )
        self.response_add_attached_reference(
            root, "RequestedUnattachedReference", assertion_proc._assertion_id
        )

        token_type = SubElement(root, f"{{{NS_WS_FED_TRUST}}}TokenType")
        token_type.text = WSS_TOKEN_TYPE_SAML2

        request_type = SubElement(root, f"{{{NS_WS_FED_TRUST}}}RequestType")
        request_type.text = "http://schemas.xmlsoap.org/ws/2005/02/trust/Issue"

        key_type = SubElement(root, f"{{{NS_WS_FED_TRUST}}}KeyType")
        key_type.text = "http://schemas.xmlsoap.org/ws/2005/05/identity/NoProofKey"

        return root

    def response_add_lifetime(self, root: Element):
        """Add Lifetime element"""
        lifetime = SubElement(root, f"{{{NS_WS_FED_TRUST}}}Lifetime", nsmap=NS_MAP)
        created = SubElement(lifetime, f"{{{NS_WSS_UTILITY}}}Created")
        created.text = get_time_string()
        expires = SubElement(lifetime, f"{{{NS_WSS_UTILITY}}}Expires")
        expires.text = get_time_string(
            timedelta_from_string(self.provider.session_valid_not_on_or_after)
        )

    def response_add_applies_to(self, root: Element):
        """Add AppliesTo element"""
        applies_to = SubElement(root, f"{{{NS_POLICY}}}AppliesTo")
        endpont_ref = SubElement(applies_to, f"{{{NS_ADDRESSING}}}EndpointReference")
        address = SubElement(endpont_ref, f"{{{NS_ADDRESSING}}}Address")
        address.text = self.sign_in_request.wtrealm

    def response_add_requested_security_token(self, root: Element):
        """Add RequestedSecurityToken and child assertion"""
        token = SubElement(root, f"{{{NS_WS_FED_TRUST}}}RequestedSecurityToken")
        req = AuthNRequest()
        proc = AssertionProcessor(self.provider, self.request, req)
        proc.provider.audience = self.sign_in_request.wtrealm
        token.append(proc.get_assertion())

        return proc

    def response_add_attached_reference(self, root: Element, tag: str, value: str):
        ref = SubElement(root, f"{{{NS_WS_FED_TRUST}}}{tag}")
        sec_token_ref = SubElement(ref, f"{{{NS_WSS_SEC}}}SecurityTokenReference")
        sec_token_ref.attrib[f"{{{NS_WSS_D3P1}}}TokenType"] = WSS_TOKEN_TYPE_SAML2

        key_identifier = SubElement(sec_token_ref, f"{{{NS_WSS_SEC}}}KeyIdentifier")
        key_identifier.attrib["ValueType"] = WSS_KEY_IDENTIFIER_SAML_ID
        key_identifier.text = value

    def response(self) -> dict[str, str]:
        root = self.create_response_token()
        assertion = root.xpath("//saml:Assertion", namespaces=NS_MAP)[0]
        AssertionProcessor(self.provider, self.request, AuthNRequest())._sign(assertion)
        str_token = etree.tostring(root).decode("utf-8")  # nosec
        return delete_none_values(
            {
                WS_FED_POST_KEY_ACTION: WS_FED_ACTION_SIGN_IN,
                WS_FED_POST_KEY_RESULT: str_token,
                WS_FED_POST_KEY_CONTEXT: self.sign_in_request.wctx,
            }
        )
