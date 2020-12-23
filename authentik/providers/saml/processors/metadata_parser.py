"""SAML ServiceProvider Metadata Parser and dataclass"""
from base64 import b64decode
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote_plus

import xmlsec
from defusedxml import ElementTree
from lxml import etree  # nosec
from structlog import get_logger

from authentik.providers.saml.exceptions import CannotHandleAssertion
from authentik.providers.saml.models import SAMLBindings, SAMLProvider
from authentik.providers.saml.utils.encoding import decode_base64_and_inflate
from authentik.sources.saml.processors.constants import (
    DSA_SHA1,
    NS_MAP, NS_SAML_METADATA,
    NS_SAML_PROTOCOL,
    RSA_SHA1,
    RSA_SHA256,
    RSA_SHA384,
    RSA_SHA512, SAML_BINDING_POST, SAML_BINDING_REDIRECT,
    SAML_NAME_ID_FORMAT_EMAIL,
)

LOGGER = get_logger()


@dataclass
class ServiceProviderMetadata:
    """SP Metadata Dataclass"""

    entity_id: str

    acs_binding: SAMLBindings
    acs_location: str

    auth_n_request_signed: bool
    assertion_signed: bool

    def to_provider(self, name: str) -> SAMLProvider:
        """Create a SAMLProvider instance from the details. `name` is required,
        as depending on the metadata CertificateKeypairs might have to be created."""
        provider = SAMLProvider(name=name)
        provider.issuer = self.entity_id
        provider.sp_binding = self.acs_binding
        provider.acs_url = self.acs_location

        # TODO: auth_n_request_signed
        # TODO: assertion_signed

        return provider


class ServiceProviderMetadataParser:
    """Service-Provider Metadata Parser"""

    @staticmethod
    def parse(decoded_xml: str) -> ServiceProviderMetadata:
        root = ElementTree.fromstring(decoded_xml)

        entity_id = root.attrib["entityID"]
        sp_sso_descriptors = root.findall(f"{{{NS_SAML_METADATA}}}SPSSODescriptor")
        if len(sp_sso_descriptors) < 1:
            raise ValueError("no SPSSODescriptor objects found.")
        # For now we'll only look at the first descriptor.
        # Even if multiple descriptors exist, we can only configure one
        descriptor = sp_sso_descriptors[0]
        auth_n_request_signed = descriptor.attrib["AuthnRequestsSigned"]
        assertion_signed = descriptor.attrib["WantAssertionsSigned"]

        acs_services = descriptor.findall(f"{{{NS_SAML_METADATA}}}AssertionConsumerService")
        if len(acs_services) < 1:
            raise ValueError("No AssertionConsumerService found.")

        acs_service = acs_services[0]
        acs_binding = {
            SAML_BINDING_REDIRECT: SAMLBindings.REDIRECT,
            SAML_BINDING_POST: SAMLBindings.POST
        }[acs_service.attrib["Binding"]]
        acs_location = acs_service.attrib["Location"]

        return ServiceProviderMetadata(
            entity_id=entity_id,
            acs_binding=acs_binding,
            acs_location=acs_location,
            auth_n_request_signed=auth_n_request_signed,
            assertion_signed=assertion_signed,
        )
