"""SAML Service Provider Metadata Processor"""

from collections.abc import Iterator

from django.http import HttpRequest
from lxml.etree import Element, SubElement, tostring  # nosec

from authentik.common.saml.constants import (
    NS_MAP,
    NS_SAML_METADATA,
    NS_SIGNATURE,
    SAML_BINDING_POST,
)
from authentik.providers.saml.utils.encoding import strip_pem_header
from authentik.providers.saml.utils.keyring import candidate_cert_pems
from authentik.sources.saml.models import SAMLSource


class MetadataProcessor:
    """SAML Service Provider Metadata Processor"""

    source: SAMLSource
    http_request: HttpRequest

    def __init__(self, source: SAMLSource, request: HttpRequest):
        self.source = source
        self.http_request = request

    def _build_key_descriptor(self, pem: str, use: str) -> Element:
        """Build one KeyDescriptor from PEM and use token."""
        key_descriptor = Element(f"{{{NS_SAML_METADATA}}}KeyDescriptor")
        key_descriptor.attrib["use"] = use
        key_info = SubElement(key_descriptor, f"{{{NS_SIGNATURE}}}KeyInfo")
        x509_data = SubElement(key_info, f"{{{NS_SIGNATURE}}}X509Data")
        x509_certificate = SubElement(x509_data, f"{{{NS_SIGNATURE}}}X509Certificate")
        x509_certificate.text = strip_pem_header(pem.replace("\r", "")).replace("\n", "")
        return key_descriptor

    def iter_signing_key_descriptors(self) -> Iterator[Element]:
        """Yield signing KeyDescriptor entries (single KP first, else ring order)."""
        for pem in candidate_cert_pems(
            kp=self.source.signing_kp,
            ring=getattr(self.source, "signing_kp_ring", None),
        ):
            yield self._build_key_descriptor(pem, "signing")

    def iter_encryption_key_descriptors(self) -> Iterator[Element]:
        """Yield encryption KeyDescriptor entries (single KP first, else ring order)."""
        for pem in candidate_cert_pems(
            kp=self.source.encryption_kp,
            ring=getattr(self.source, "encryption_kp_ring", None),
        ):
            yield self._build_key_descriptor(pem, "encryption")

    # Using type unions doesn't work with cython types (which is what lxml is)
    def get_signing_key_descriptor(self) -> Element | None:  # noqa: UP007
        """Get first signing KeyDescriptor, if enabled for the source."""
        return next(self.iter_signing_key_descriptors(), None)

    def get_encryption_key_descriptor(self) -> Element | None:  # noqa: UP007
        """Get first encryption KeyDescriptor, if enabled for the source."""
        return next(self.iter_encryption_key_descriptors(), None)

    def get_name_id_format(self) -> Element:
        element = Element(f"{{{NS_SAML_METADATA}}}NameIDFormat")
        element.text = self.source.name_id_policy
        return element

    def build_entity_descriptor(self) -> str:
        """Build full EntityDescriptor"""
        entity_descriptor = Element(f"{{{NS_SAML_METADATA}}}EntityDescriptor", nsmap=NS_MAP)
        entity_descriptor.attrib["entityID"] = self.source.get_issuer(self.http_request)

        sp_sso_descriptor = SubElement(entity_descriptor, f"{{{NS_SAML_METADATA}}}SPSSODescriptor")
        sp_sso_descriptor.attrib["protocolSupportEnumeration"] = (
            "urn:oasis:names:tc:SAML:2.0:protocol"
        )

        for signing_descriptor in self.iter_signing_key_descriptors():
            sp_sso_descriptor.append(signing_descriptor)

        for encryption_descriptor in self.iter_encryption_key_descriptors():
            sp_sso_descriptor.append(encryption_descriptor)

        sp_sso_descriptor.append(self.get_name_id_format())

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
