"""SAML Service Provider Metadata Processor"""
from typing import Iterator, Optional

from django.http import HttpRequest
from lxml.etree import Element, SubElement, tostring  # nosec

from authentik.providers.saml.utils.encoding import strip_pem_header
from authentik.sources.saml.models import SAMLSource
from authentik.sources.saml.processors.constants import (
    NS_MAP,
    NS_SAML_METADATA,
    NS_SIGNATURE,
    SAML_BINDING_POST,
    SAML_NAME_ID_FORMAT_EMAIL,
    SAML_NAME_ID_FORMAT_PERSISTENT,
    SAML_NAME_ID_FORMAT_TRANSIENT,
    SAML_NAME_ID_FORMAT_WINDOWS,
    SAML_NAME_ID_FORMAT_X509,
)


class MetadataProcessor:
    """SAML Service Provider Metadata Processor"""

    source: SAMLSource
    http_request: HttpRequest

    def __init__(self, source: SAMLSource, request: HttpRequest):
        self.source = source
        self.http_request = request

    def get_signing_key_descriptor(self) -> Optional[Element]:
        """Get Signing KeyDescriptor, if enabled for the source"""
        if self.source.signing_kp:
            key_descriptor = Element(f"{{{NS_SAML_METADATA}}}KeyDescriptor")
            key_descriptor.attrib["use"] = "signing"
            key_info = SubElement(key_descriptor, f"{{{NS_SIGNATURE}}}KeyInfo")
            x509_data = SubElement(key_info, f"{{{NS_SIGNATURE}}}X509Data")
            x509_certificate = SubElement(x509_data, f"{{{NS_SIGNATURE}}}X509Certificate")
            x509_certificate.text = strip_pem_header(
                self.source.signing_kp.certificate_data.replace("\r", "")
            ).replace("\n", "")
            return key_descriptor
        return None

    def get_name_id_formats(self) -> Iterator[Element]:
        """Get compatible NameID Formats"""
        formats = [
            SAML_NAME_ID_FORMAT_EMAIL,
            SAML_NAME_ID_FORMAT_PERSISTENT,
            SAML_NAME_ID_FORMAT_X509,
            SAML_NAME_ID_FORMAT_WINDOWS,
            SAML_NAME_ID_FORMAT_TRANSIENT,
        ]
        for name_id_format in formats:
            element = Element(f"{{{NS_SAML_METADATA}}}NameIDFormat")
            element.text = name_id_format
            yield element

    def build_entity_descriptor(self) -> str:
        """Build full EntityDescriptor"""
        entity_descriptor = Element(f"{{{NS_SAML_METADATA}}}EntityDescriptor", nsmap=NS_MAP)
        entity_descriptor.attrib["entityID"] = self.source.get_issuer(self.http_request)

        sp_sso_descriptor = SubElement(entity_descriptor, f"{{{NS_SAML_METADATA}}}SPSSODescriptor")
        sp_sso_descriptor.attrib[
            "protocolSupportEnumeration"
        ] = "urn:oasis:names:tc:SAML:2.0:protocol"

        signing_descriptor = self.get_signing_key_descriptor()
        if signing_descriptor is not None:
            sp_sso_descriptor.append(signing_descriptor)

        for name_id_format in self.get_name_id_formats():
            sp_sso_descriptor.append(name_id_format)

        assertion_consumer_service = SubElement(
            sp_sso_descriptor, f"{{{NS_SAML_METADATA}}}AssertionConsumerService"
        )
        assertion_consumer_service.attrib["isDefault"] = "true"
        assertion_consumer_service.attrib["index"] = "0"
        assertion_consumer_service.attrib["Binding"] = SAML_BINDING_POST
        assertion_consumer_service.attrib["Location"] = self.source.build_full_url(
            self.http_request
        )

        return tostring(entity_descriptor).decode()
