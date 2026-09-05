"""SAML ServiceProvider Metadata Parser and dataclass"""

from dataclasses import dataclass

import xmlsec
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import InvalidVersion, load_pem_x509_certificate
from defusedxml.lxml import fromstring
from lxml import etree  # nosec
from structlog.stdlib import get_logger

from authentik.common.saml.constants import NS_MAP, NS_SAML_METADATA
from authentik.crypto.models import CertificateKeyPair, format_cert
from authentik.flows.models import Flow
from authentik.providers.saml.models import SAMLBindings, SAMLPropertyMapping, SAMLProvider
from authentik.sources.saml.models import SAMLNameIDPolicy

LOGGER = get_logger()

# Which binding to pick when metadata advertises an endpoint for more than one of them.
# POST is preferred as the Redirect binding must not be used to deliver a Response
# (SAML 2.0 Profiles, 4.1.2) and only a POST SLS binding allows back-channel logout.
BINDING_PREFERENCE = (SAMLBindings.POST, SAMLBindings.REDIRECT)


@dataclass(slots=True)
class ServiceProviderMetadata:
    """SP Metadata Dataclass"""

    entity_id: str

    acs_binding: str
    acs_location: str

    auth_n_request_signed: bool
    assertion_signed: bool
    name_id_policy: SAMLNameIDPolicy

    signing_keypair: CertificateKeyPair | None = None
    encryption_keypair: CertificateKeyPair | None = None

    # Single Logout Service (optional)
    sls_binding: str | None = None
    sls_location: str | None = None

    def to_provider(
        self, name: str, authorization_flow: Flow, invalidation_flow: Flow
    ) -> SAMLProvider:
        """Create a SAMLProvider instance from the details. `name` is required,
        as depending on the metadata CertificateKeypairs might have to be created."""
        provider = SAMLProvider.objects.create(
            name=name, authorization_flow=authorization_flow, invalidation_flow=invalidation_flow
        )
        provider.sp_binding = self.acs_binding
        provider.acs_url = self.acs_location
        provider.audience = self.entity_id
        provider.default_name_id_policy = self.name_id_policy
        # Single Logout Service
        if self.sls_location:
            provider.sls_url = self.sls_location
        if self.sls_binding:
            provider.sls_binding = self.sls_binding
        if self.signing_keypair and self.auth_n_request_signed:
            self.signing_keypair.name = f"Provider {name} - SAML Signing Certificate"
            self.signing_keypair.save()
            provider.verification_kp = self.signing_keypair
        if self.encryption_keypair:
            self.encryption_keypair.name = f"Provider {name} - SAML Encryption Certificate"
            self.encryption_keypair.save()
            provider.encryption_kp = self.encryption_keypair
        if self.assertion_signed:
            provider.signing_kp = CertificateKeyPair.objects.exclude(key_data__iexact="").first()
        # Set all auto-generated Property-mappings as defaults
        # They should provide a sane default for most applications:
        provider.property_mappings.set(SAMLPropertyMapping.objects.exclude(managed__isnull=True))
        provider.save()
        return provider


class ServiceProviderMetadataParser:
    """Service-Provider Metadata Parser"""

    def get_signing_cert(self, root: etree.Element) -> CertificateKeyPair | None:
        """Extract signing X509Certificate from metadata, when given."""
        signing_certs = root.xpath(
            '//md:SPSSODescriptor/md:KeyDescriptor[@use="signing"]//ds:X509Certificate/text()',
            namespaces=NS_MAP,
        )
        if len(signing_certs) < 1:
            return None
        raw_cert = format_cert(signing_certs[0])
        # sanity check, make sure the certificate is valid.
        try:
            load_pem_x509_certificate(raw_cert.encode("utf-8"), default_backend())
        except InvalidVersion as exc:
            raise ValueError("Certificate in metadata is not a valid X.509 version") from exc
        return CertificateKeyPair(
            certificate_data=raw_cert,
        )

    def get_encryption_cert(self, root: etree.Element) -> CertificateKeyPair | None:
        """Extract encryption X509Certificate from metadata, when given."""
        encryption_certs = root.xpath(
            '//md:SPSSODescriptor/md:KeyDescriptor[@use="encryption"]//ds:X509Certificate/text()',
            namespaces=NS_MAP,
        )
        if len(encryption_certs) < 1:
            return None
        raw_cert = format_cert(encryption_certs[0])
        # sanity check, make sure the certificate is valid.
        try:
            load_pem_x509_certificate(raw_cert.encode("utf-8"), default_backend())
        except InvalidVersion as exc:
            raise ValueError("Certificate in metadata is not a valid X.509 version") from exc
        return CertificateKeyPair(
            certificate_data=raw_cert,
        )

    def select_endpoint(
        self, endpoints: list[etree.Element]
    ) -> tuple[SAMLBindings, str] | tuple[None, None]:
        """Select the endpoint authentik should use out of `endpoints`, ignoring any endpoint
        with a binding we don't support. Endpoints are picked by `BINDING_PREFERENCE` first,
        then by `isDefault`, and lastly by the order they're listed in."""
        supported = []
        for endpoint in endpoints:
            binding = SAMLBindings.from_metadata_binding(endpoint.attrib.get("Binding"))
            location = endpoint.attrib.get("Location")
            if not binding or not location:
                LOGGER.debug(
                    "Skipping endpoint with unsupported binding",
                    binding=endpoint.attrib.get("Binding"),
                    location=location,
                )
                continue
            supported.append((endpoint, binding, location))
        if not supported:
            return None, None
        # sorted() is stable, so endpoints that tie keep the order they're listed in
        endpoint, binding, location = sorted(
            supported,
            key=lambda endpoint: (
                BINDING_PREFERENCE.index(endpoint[1]),
                endpoint[0].attrib.get("isDefault", "").lower() != "true",
            ),
        )[0]
        return binding, location

    def check_signature(self, root: etree.Element, keypair: CertificateKeyPair):
        """If Metadata is signed, check validity of signature"""
        xmlsec.tree.add_ids(root, ["ID"])
        signature_nodes = root.xpath("/md:EntityDescriptor/ds:Signature", namespaces=NS_MAP)
        if len(signature_nodes) != 1:
            # No Signature
            return

        signature_node = signature_nodes[0]

        if signature_node is not None:
            try:
                ctx = xmlsec.SignatureContext()
                key = xmlsec.Key.from_memory(
                    keypair.certificate_data,
                    xmlsec.constants.KeyDataFormatCertPem,
                    None,
                )
                ctx.key = key
                ctx.verify(signature_node)
            except xmlsec.Error as exc:
                raise ValueError("Failed to verify Metadata signature") from exc

    def parse(self, raw_xml: str) -> ServiceProviderMetadata:
        """Parse raw XML to ServiceProviderMetadata"""
        root = fromstring(raw_xml.encode())

        entity_id = root.attrib["entityID"]
        sp_sso_descriptors = root.findall(f"{{{NS_SAML_METADATA}}}SPSSODescriptor")
        if len(sp_sso_descriptors) < 1:
            raise ValueError("no SPSSODescriptor objects found.")
        # For now we'll only look at the first descriptor.
        # Even if multiple descriptors exist, we can only configure one
        descriptor = sp_sso_descriptors[0]
        auth_n_request_signed = False
        if "AuthnRequestsSigned" in descriptor.attrib:
            auth_n_request_signed = descriptor.attrib["AuthnRequestsSigned"].lower() == "true"

        assertion_signed = False
        if "WantAssertionsSigned" in descriptor.attrib:
            assertion_signed = descriptor.attrib["WantAssertionsSigned"].lower() == "true"

        acs_services = descriptor.findall(f"{{{NS_SAML_METADATA}}}AssertionConsumerService")
        if len(acs_services) < 1:
            raise ValueError("No AssertionConsumerService found.")

        acs_binding, acs_location = self.select_endpoint(acs_services)
        if not acs_binding:
            raise ValueError(
                "No AssertionConsumerService with a supported binding found. "
                "Only HTTP-POST and HTTP-Redirect are supported."
            )

        signing_keypair = self.get_signing_cert(root)
        if signing_keypair:
            self.check_signature(root, signing_keypair)
        encryption_keypair = self.get_encryption_cert(root)

        # Use the first NameIDFormat we support, formats we don't know are skipped
        name_id_policy = SAMLNameIDPolicy.UNSPECIFIED
        for name_id_format in descriptor.findall(f"{{{NS_SAML_METADATA}}}NameIDFormat"):
            if name_id_format.text in SAMLNameIDPolicy.values:
                name_id_policy = SAMLNameIDPolicy(name_id_format.text)
                break
            LOGGER.debug("Skipping unsupported NameIDFormat", name_id_format=name_id_format.text)

        # Parse SingleLogoutService (not always present)
        sls_services = descriptor.findall(f"{{{NS_SAML_METADATA}}}SingleLogoutService")
        sls_binding, sls_location = self.select_endpoint(sls_services)

        return ServiceProviderMetadata(
            entity_id=entity_id,
            acs_binding=acs_binding,
            acs_location=acs_location,
            auth_n_request_signed=auth_n_request_signed,
            assertion_signed=assertion_signed,
            signing_keypair=signing_keypair,
            encryption_keypair=encryption_keypair,
            name_id_policy=name_id_policy,
            sls_binding=sls_binding,
            sls_location=sls_location,
        )
