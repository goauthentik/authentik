"""SAML AuthnRequest Processor"""
from defusedxml import ElementTree
from django.http import HttpRequest
from lxml.etree import Element  # nosec

from passbook.providers.saml.utils import get_random_id
from passbook.providers.saml.utils.time import get_time_string
from passbook.sources.saml.models import SAMLSource
from passbook.sources.saml.processors.constants import (
    NS_MAP,
    NS_SAML_ASSERTION,
    NS_SAML_PROTOCOL,
)


class RequestProcessor:
    """SAML AuthnRequest Processor"""

    source: SAMLSource
    http_request: HttpRequest

    def __init__(self, source: SAMLSource, request: HttpRequest):
        self.source = source
        self.http_request = request

    def get_issuer(self) -> Element:
        """Get Issuer Element"""
        issuer = Element(f"{{{NS_SAML_ASSERTION}}}Issuer")
        issuer.text = self.source.get_issuer(self.http_request)
        return issuer

    def get_name_id_policy(self) -> Element:
        """Get NameID Policy Element"""
        name_id_policy = Element(f"{{{NS_SAML_PROTOCOL}}}NameIDPolicy")
        name_id_policy.text = self.source.name_id_policy
        return name_id_policy

    def build_auth_n(self) -> str:
        """Get full AuthnRequest"""
        auth_n_request = Element(f"{{{NS_SAML_PROTOCOL}}}AuthnRequest", nsmap=NS_MAP)
        auth_n_request.attrib[
            "AssertionConsumerServiceURL"
        ] = self.source.build_full_url(self.http_request)
        auth_n_request.attrib["Destination"] = self.source.sso_url
        auth_n_request.attrib["ID"] = get_random_id()
        auth_n_request.attrib["IssueInstant"] = get_time_string()
        auth_n_request.attrib["ProtocolBinding"] = self.source.binding_type
        auth_n_request.attrib["Version"] = "2.0"
        # Create issuer object
        auth_n_request.append(self.get_issuer())
        # Create NameID Policy Object
        auth_n_request.append(self.get_name_id_policy())
        return ElementTree.tostring(auth_n_request).decode()
