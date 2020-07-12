"""SAML Identity Provider Metadata Processor"""
from typing import Iterator, Optional

from defusedxml import ElementTree
from django.http import HttpRequest
from django.shortcuts import reverse
from lxml.etree import Element, SubElement  # nosec
from signxml.util import strip_pem_header

from passbook.providers.saml.models import SAMLProvider
from passbook.sources.saml.processors.constants import (
    NS_MAP,
    NS_SAML_METADATA,
    NS_SIGNATURE,
    SAML_BINDING_POST,
    SAML_BINDING_REDIRECT,
    SAML_NAME_ID_FORMAT_EMAIL,
    SAML_NAME_ID_FORMAT_PERSISTENT,
    SAML_NAME_ID_FORMAT_TRANSIENT,
    SAML_NAME_ID_FORMAT_X509,
)


class MetadataProcessor:
    """SAML Identity Provider Metadata Processor"""

    provider: SAMLProvider
    http_request: HttpRequest

    def __init__(self, provider: SAMLProvider, request: HttpRequest):
        self.provider = provider
        self.http_request = request

    def get_signing_key_descriptor(self) -> Optional[Element]:
        """Get Singing KeyDescriptor, if enabled for the provider"""
        if self.provider.signing_kp:
            key_descriptor = Element(f"{{{NS_SAML_METADATA}}}KeyDescriptor")
            key_descriptor.attrib["use"] = "signing"
            key_info = SubElement(key_descriptor, f"{{{NS_SIGNATURE}}}KeyInfo")
            x509_data = SubElement(key_info, f"{{{NS_SIGNATURE}}}X509Data")
            x509_certificate = SubElement(
                x509_data, f"{{{NS_SIGNATURE}}}X509Certificate"
            )
            x509_certificate.text = strip_pem_header(
                self.provider.signing_kp.certificate_data.replace("\r", "")
            ).replace("\n", "")
            return key_descriptor
        return None

    def get_name_id_formats(self) -> Iterator[Element]:
        """Get compatible NameID Formats"""
        formats = [
            SAML_NAME_ID_FORMAT_EMAIL,
            SAML_NAME_ID_FORMAT_PERSISTENT,
            SAML_NAME_ID_FORMAT_X509,
            SAML_NAME_ID_FORMAT_TRANSIENT,
        ]
        for name_id_format in formats:
            element = Element(f"{{{NS_SAML_METADATA}}}NameIDFormat")
            element.text = name_id_format
            yield element

    def get_bindings(self) -> Iterator[Element]:
        """Get all Bindings supported"""
        binding_url_map = {
            SAML_BINDING_POST: self.http_request.build_absolute_uri(
                reverse(
                    "passbook_providers_saml:sso-post",
                    kwargs={"application_slug": self.provider.application.slug},
                )
            ),
            SAML_BINDING_REDIRECT: self.http_request.build_absolute_uri(
                reverse(
                    "passbook_providers_saml:sso-redirect",
                    kwargs={"application_slug": self.provider.application.slug},
                )
            ),
        }
        for binding, url in binding_url_map.items():
            element = Element(f"{{{NS_SAML_METADATA}}}SingleSignOnService")
            element.attrib["Binding"] = binding
            element.attrib["Location"] = url
            yield element

    def build_entity_descriptor(self) -> str:
        """Build full EntityDescriptor"""
        entity_descriptor = Element(
            f"{{{NS_SAML_METADATA}}}EntityDescriptor", nsmap=NS_MAP
        )
        entity_descriptor.attrib["entityID"] = self.provider.issuer

        idp_sso_descriptor = SubElement(
            entity_descriptor, f"{{{NS_SAML_METADATA}}}IDPSSODescriptor"
        )
        idp_sso_descriptor.attrib[
            "protocolSupportEnumeration"
        ] = "urn:oasis:names:tc:SAML:2.0:protocol"

        signing_descriptor = self.get_signing_key_descriptor()
        if signing_descriptor is not None:
            idp_sso_descriptor.append(signing_descriptor)

        for name_id_format in self.get_name_id_formats():
            idp_sso_descriptor.append(name_id_format)

        for binding in self.get_bindings():
            idp_sso_descriptor.append(binding)

        return ElementTree.tostring(entity_descriptor).decode()
