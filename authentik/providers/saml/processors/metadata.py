"""SAML Identity Provider Metadata Processor"""
from hashlib import sha256
from typing import Iterator, Optional

import xmlsec  # nosec
from django.http import HttpRequest
from django.urls import reverse
from lxml.etree import Element, SubElement, tostring  # nosec

from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.utils.encoding import strip_pem_header
from authentik.sources.saml.processors.constants import (
    DIGEST_ALGORITHM_TRANSLATION_MAP,
    NS_MAP,
    NS_SAML_METADATA,
    NS_SAML_PROTOCOL,
    NS_SIGNATURE,
    SAML_BINDING_POST,
    SAML_BINDING_REDIRECT,
    SAML_NAME_ID_FORMAT_EMAIL,
    SAML_NAME_ID_FORMAT_PERSISTENT,
    SAML_NAME_ID_FORMAT_TRANSIENT,
    SAML_NAME_ID_FORMAT_X509,
    SIGN_ALGORITHM_TRANSFORM_MAP,
)


class MetadataProcessor:
    """SAML Identity Provider Metadata Processor"""

    provider: SAMLProvider
    http_request: HttpRequest
    force_binding: Optional[str]

    def __init__(self, provider: SAMLProvider, request: HttpRequest):
        self.provider = provider
        self.http_request = request
        self.force_binding = None
        self.xml_id = "_" + sha256(f"{provider.name}-{provider.pk}".encode("ascii")).hexdigest()

    def get_signing_key_descriptor(self) -> Optional[Element]:
        """Get Signing KeyDescriptor, if enabled for the provider"""
        if not self.provider.signing_kp:
            return None
        key_descriptor = Element(f"{{{NS_SAML_METADATA}}}KeyDescriptor")
        key_descriptor.attrib["use"] = "signing"
        key_info = SubElement(key_descriptor, f"{{{NS_SIGNATURE}}}KeyInfo")
        x509_data = SubElement(key_info, f"{{{NS_SIGNATURE}}}X509Data")
        x509_certificate = SubElement(x509_data, f"{{{NS_SIGNATURE}}}X509Certificate")
        x509_certificate.text = strip_pem_header(
            self.provider.signing_kp.certificate_data.replace("\r", "")
        )
        return key_descriptor

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

    def get_sso_bindings(self) -> Iterator[Element]:
        """Get all Bindings supported"""
        binding_url_map = {
            (SAML_BINDING_REDIRECT, "SingleSignOnService"): self.http_request.build_absolute_uri(
                reverse(
                    "authentik_providers_saml:sso-redirect",
                    kwargs={"application_slug": self.provider.application.slug},
                )
            ),
            (SAML_BINDING_POST, "SingleSignOnService"): self.http_request.build_absolute_uri(
                reverse(
                    "authentik_providers_saml:sso-post",
                    kwargs={"application_slug": self.provider.application.slug},
                )
            ),
        }
        for binding_svc, url in binding_url_map.items():
            binding, svc = binding_svc
            if self.force_binding and self.force_binding != binding:
                continue
            element = Element(f"{{{NS_SAML_METADATA}}}{svc}")
            element.attrib["Binding"] = binding
            element.attrib["Location"] = url
            yield element

    def get_slo_bindings(self) -> Iterator[Element]:
        """Get all Bindings supported"""
        binding_url_map = {
            (SAML_BINDING_REDIRECT, "SingleLogoutService"): self.http_request.build_absolute_uri(
                reverse(
                    "authentik_providers_saml:slo-redirect",
                    kwargs={"application_slug": self.provider.application.slug},
                )
            ),
            (SAML_BINDING_POST, "SingleLogoutService"): self.http_request.build_absolute_uri(
                reverse(
                    "authentik_providers_saml:slo-post",
                    kwargs={"application_slug": self.provider.application.slug},
                )
            ),
        }
        for binding_svc, url in binding_url_map.items():
            binding, svc = binding_svc
            if self.force_binding and self.force_binding != binding:
                continue
            element = Element(f"{{{NS_SAML_METADATA}}}{svc}")
            element.attrib["Binding"] = binding
            element.attrib["Location"] = url
            yield element

    def _prepare_signature(self, entity_descriptor: Element):
        sign_algorithm_transform = SIGN_ALGORITHM_TRANSFORM_MAP.get(
            self.provider.signature_algorithm, xmlsec.constants.TransformRsaSha1
        )
        signature = xmlsec.template.create(
            entity_descriptor,
            xmlsec.constants.TransformExclC14N,
            sign_algorithm_transform,
            ns="ds",  # type: ignore
        )
        entity_descriptor.append(signature)

    def _sign(self, entity_descriptor: Element):
        digest_algorithm_transform = DIGEST_ALGORITHM_TRANSLATION_MAP.get(
            self.provider.digest_algorithm, xmlsec.constants.TransformSha1
        )
        assertion = entity_descriptor.xpath("//md:EntityDescriptor", namespaces=NS_MAP)[0]
        xmlsec.tree.add_ids(assertion, ["ID"])
        signature_node = xmlsec.tree.find_node(assertion, xmlsec.constants.NodeSignature)
        ref = xmlsec.template.add_reference(
            signature_node,
            digest_algorithm_transform,
            uri="#" + self.xml_id,
        )
        xmlsec.template.add_transform(ref, xmlsec.constants.TransformEnveloped)
        xmlsec.template.add_transform(ref, xmlsec.constants.TransformExclC14N)
        key_info = xmlsec.template.ensure_key_info(signature_node)
        xmlsec.template.add_x509_data(key_info)

        ctx = xmlsec.SignatureContext()

        key = xmlsec.Key.from_memory(
            self.provider.signing_kp.key_data,
            xmlsec.constants.KeyDataFormatPem,
            None,
        )
        key.load_cert_from_memory(
            self.provider.signing_kp.certificate_data,
            xmlsec.constants.KeyDataFormatCertPem,
        )
        ctx.key = key
        ctx.sign(signature_node)

    def build_entity_descriptor(self) -> str:
        """Build full EntityDescriptor"""
        entity_descriptor = Element(f"{{{NS_SAML_METADATA}}}EntityDescriptor", nsmap=NS_MAP)
        entity_descriptor.attrib["ID"] = self.xml_id
        entity_descriptor.attrib["entityID"] = self.provider.issuer

        if self.provider.signing_kp:
            self._prepare_signature(entity_descriptor)

        idp_sso_descriptor = SubElement(
            entity_descriptor, f"{{{NS_SAML_METADATA}}}IDPSSODescriptor"
        )
        idp_sso_descriptor.attrib["protocolSupportEnumeration"] = NS_SAML_PROTOCOL
        if self.provider.verification_kp:
            idp_sso_descriptor.attrib["WantAuthnRequestsSigned"] = "true"

        signing_descriptor = self.get_signing_key_descriptor()
        if signing_descriptor is not None:
            idp_sso_descriptor.append(signing_descriptor)

        for binding in self.get_slo_bindings():
            idp_sso_descriptor.append(binding)

        for name_id_format in self.get_name_id_formats():
            idp_sso_descriptor.append(name_id_format)

        for binding in self.get_sso_bindings():
            idp_sso_descriptor.append(binding)

        if self.provider.signing_kp:
            self._sign(entity_descriptor)

        return tostring(entity_descriptor).decode()
