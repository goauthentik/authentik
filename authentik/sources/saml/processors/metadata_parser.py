"""SAML IdentityProvider Metadata Parser and dataclass"""

from dataclasses import dataclass

from cryptography.hazmat.backends import default_backend
from cryptography.x509 import InvalidVersion, load_pem_x509_certificate
from lxml import etree  # nosec
from structlog.stdlib import get_logger

from authentik.common.saml.constants import (
    NS_MAP,
    NS_SAML_METADATA,
    SAML_BINDING_POST,
    SAML_BINDING_REDIRECT,
)
from authentik.crypto.models import CertificateKeyPair, format_cert
from authentik.lib.xml import lxml_from_string
from authentik.providers.saml.processors.metadata_parser import ServiceProviderMetadataParser
from authentik.sources.saml.models import SAMLBindingTypes, SAMLNameIDPolicy, SAMLSource

LOGGER = get_logger()

# Which binding to pick when metadata advertises an endpoint for more than one of them.
# Redirect is the source's default.
BINDING_PREFERENCE = (SAML_BINDING_REDIRECT, SAML_BINDING_POST)
BINDING_TYPES = {
    SAML_BINDING_REDIRECT: SAMLBindingTypes.REDIRECT,
    SAML_BINDING_POST: SAMLBindingTypes.POST,
}


@dataclass(slots=True)
class IdentityProviderMetadata:
    """IdP Metadata Dataclass"""

    entity_id: str

    sso_binding: str
    sso_location: str

    slo_location: str | None = None
    name_id_formats: list[SAMLNameIDPolicy] | None = None
    signing_keypair: CertificateKeyPair | None = None

    def apply_to_source(self, source: SAMLSource) -> bool:
        """Apply the metadata to `source` without saving it. Returns whether anything changed."""
        changed = False
        binding_type = BINDING_TYPES[self.sso_binding]
        # Keep the auto-submitting POST variant if the administrator chose it
        if (
            binding_type == SAMLBindingTypes.POST
            and source.binding_type == SAMLBindingTypes.POST_AUTO
        ):
            binding_type = SAMLBindingTypes.POST_AUTO
        # The metadata lists the formats the IdP supports, so only replace the configured
        # policy when the IdP doesn't support it
        name_id_policy = source.name_id_policy
        if self.name_id_formats and name_id_policy not in self.name_id_formats:
            name_id_policy = self.name_id_formats[0]
        for attr, value in (
            ("sso_url", self.sso_location),
            ("binding_type", binding_type),
            ("slo_url", self.slo_location),
            ("name_id_policy", name_id_policy),
        ):
            if getattr(source, attr) != value:
                setattr(source, attr, value)
                changed = True
        if self.signing_keypair:
            existing: CertificateKeyPair | None = source.verification_kp
            if existing:
                if (
                    existing.certificate_data.strip()
                    != self.signing_keypair.certificate_data.strip()
                ):
                    existing.certificate_data = self.signing_keypair.certificate_data
                    existing.save()
                    changed = True
            else:
                self.signing_keypair.name = f"Source {source.name} - SAML Signing Certificate"
                self.signing_keypair.save()
                source.verification_kp = self.signing_keypair
                changed = True
        return changed


class IdentityProviderMetadataParser:
    """Identity-Provider Metadata Parser"""

    def get_signing_cert(self, descriptor: etree.Element) -> CertificateKeyPair | None:
        """Extract the signing X509Certificate from the IDPSSODescriptor, when given.
        A KeyDescriptor without a `use` attribute is valid for both signing and encryption."""
        certs = descriptor.xpath(
            'md:KeyDescriptor[@use="signing" or not(@use)]//ds:X509Certificate/text()',
            namespaces=NS_MAP,
        )
        if len(certs) < 1:
            return None
        raw_cert = format_cert(certs[0])
        try:
            load_pem_x509_certificate(raw_cert.encode("utf-8"), default_backend())
        except (InvalidVersion, ValueError) as exc:
            raise ValueError("Certificate in metadata is not a valid X.509 certificate") from exc
        return CertificateKeyPair(certificate_data=raw_cert)

    def select_endpoint(
        self, endpoints: list[etree.Element]
    ) -> tuple[str, str] | tuple[None, None]:
        """Select the endpoint authentik should use out of `endpoints`, ignoring any endpoint
        with a binding we don't support. Endpoints are picked by `BINDING_PREFERENCE` first,
        then by the order they're listed in."""
        supported = []
        for endpoint in endpoints:
            binding = endpoint.attrib.get("Binding")
            location = endpoint.attrib.get("Location")
            if binding not in BINDING_TYPES or not location:
                LOGGER.debug(
                    "Skipping endpoint with unsupported binding", binding=binding, location=location
                )
                continue
            supported.append((binding, location))
        if not supported:
            return None, None
        return sorted(supported, key=lambda endpoint: BINDING_PREFERENCE.index(endpoint[0]))[0]

    def parse(self, raw_xml: str) -> IdentityProviderMetadata:
        """Parse raw XML to IdentityProviderMetadata"""
        root = lxml_from_string(raw_xml.encode())

        entity_id = root.attrib["entityID"]
        descriptors = root.findall(f"{{{NS_SAML_METADATA}}}IDPSSODescriptor")
        if len(descriptors) < 1:
            raise ValueError("no IDPSSODescriptor objects found.")
        # Even if multiple descriptors exist, we can only configure one
        descriptor = descriptors[0]

        sso_services = descriptor.findall(f"{{{NS_SAML_METADATA}}}SingleSignOnService")
        if len(sso_services) < 1:
            raise ValueError("No SingleSignOnService found.")
        sso_binding, sso_location = self.select_endpoint(sso_services)
        if not sso_binding:
            raise ValueError(
                "No SingleSignOnService with a supported binding found. "
                "Only HTTP-POST and HTTP-Redirect are supported."
            )

        signing_keypair = self.get_signing_cert(descriptor)
        if signing_keypair:
            ServiceProviderMetadataParser().check_signature(root, signing_keypair)

        # Collect the NameIDFormats we support, formats we don't know are skipped
        name_id_formats = []
        for name_id_format in descriptor.findall(f"{{{NS_SAML_METADATA}}}NameIDFormat"):
            value = (name_id_format.text or "").strip()
            if value in SAMLNameIDPolicy.values:
                name_id_formats.append(SAMLNameIDPolicy(value))
            else:
                LOGGER.debug("Skipping unsupported NameIDFormat", name_id_format=value)

        slo_services = descriptor.findall(f"{{{NS_SAML_METADATA}}}SingleLogoutService")
        _, slo_location = self.select_endpoint(slo_services)

        return IdentityProviderMetadata(
            entity_id=entity_id,
            sso_binding=sso_binding,
            sso_location=sso_location,
            slo_location=slo_location,
            name_id_formats=name_id_formats or None,
            signing_keypair=signing_keypair,
        )
