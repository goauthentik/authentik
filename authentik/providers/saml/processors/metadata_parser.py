"""SAML ServiceProvider Metadata Parser and dataclass"""

from dataclasses import dataclass

import xmlsec
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import InvalidVersion, load_pem_x509_certificate
from lxml import etree  # nosec
from structlog.stdlib import get_logger

from authentik.common.saml.constants import NS_MAP, NS_SAML_METADATA
from authentik.crypto.models import CertificateKeyPair, CertificateKeyPairRing, format_cert
from authentik.flows.models import Flow
from authentik.lib.xml import lxml_from_string
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

    """Keys extracted from metadata."""
    signing_cert_pems: list[str] | None = None
    encryption_cert_pems: list[str] | None = None

    # Single Logout Service (optional)
    sls_binding: str | None = None
    sls_location: str | None = None

    def to_provider(
        self, name: str, authorization_flow: Flow, invalidation_flow: Flow
    ) -> SAMLProvider:
        """Create a SAMLProvider instance from the details. `name` is required,
        as depending on the metadata CertificateKeypairs might have to be created."""
        provider = SAMLProvider.objects.create(
            name=name,
            authorization_flow=authorization_flow,
            invalidation_flow=invalidation_flow,
        )
        self.apply_to_provider(provider, create_missing_rings=True)
        return provider

    def apply_to_provider(
        self, provider: SAMLProvider, *, create_missing_rings: bool = False
    ) -> None:
        provider.sp_binding = self.acs_binding
        provider.acs_url = self.acs_location
        provider.audience = self.entity_id
        provider.default_name_id_policy = self.name_id_policy

        if self.sls_location:
            provider.sls_url = self.sls_location
        if self.sls_binding:
            provider.sls_binding = self.sls_binding

        # --- verification (remote SP signing certs) ---
        if self.signing_cert_pems and not provider.verification_kp:
            if provider.verification_kp_ring is None and create_missing_rings:
                provider.verification_kp_ring = CertificateKeyPairRing.objects.create(
                    name=f"Provider {provider.name} - SAML Verification Ring",
                )
            if provider.verification_kp_ring is not None:
                provider.verification_kp_ring.sync_membership(
                    [(i, pem) for i, pem in enumerate(self.signing_cert_pems)]
                )

        # --- encryption (remote SP encryption certs) ---
        if self.encryption_cert_pems and not provider.encryption_kp:
            if provider.encryption_kp_ring is None and create_missing_rings:
                provider.encryption_kp_ring = CertificateKeyPairRing.objects.create(
                    name=f"Provider {provider.name} - SAML Encryption Ring",
                )
            if provider.encryption_kp_ring is not None:
                provider.encryption_kp_ring.sync_membership(
                    [(i, pem) for i, pem in enumerate(self.encryption_cert_pems)]
                )

        if provider.property_mappings.count() == 0:
            provider.property_mappings.set(
                SAMLPropertyMapping.objects.exclude(managed__isnull=True)
            )

        provider.save()


class ServiceProviderMetadataParser:
    """Service-Provider Metadata Parser"""

    def __init__(self, signing_certificate: CertificateKeyPair | None = None):
        """Optionally use an external certificate to verify metadata signatures."""
        self.signing_certificate = signing_certificate

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

    def get_keydescriptor_cert_pems(
        self,
        root: etree.Element,
        *,
        use: str | None,
    ) -> list[str]:
        """Extract every X509Certificate for a given KeyDescriptor use as PEM strings.

        `use="signing"`/`"encryption"` select the respective KeyDescriptors, while `use=None`
        selects KeyDescriptors with no `use` attribute (usable for either purpose)."""
        if use == "signing":
            xp = "//md:SPSSODescriptor/md:KeyDescriptor[@use='signing']//ds:X509Certificate/text()"
        elif use == "encryption":
            xp = (
                "//md:SPSSODescriptor/md:KeyDescriptor[@use='encryption']"
                "//ds:X509Certificate/text()"
            )
        elif use is None:
            xp = "//md:SPSSODescriptor/md:KeyDescriptor[not(@use)]//ds:X509Certificate/text()"
        else:
            raise ValueError("Invalid use")

        out: list[str] = []
        for b64 in root.xpath(xp, namespaces=NS_MAP):
            pem = format_cert(b64).strip()
            load_pem_x509_certificate(pem.encode("utf-8"), default_backend())  # sanity check
            out.append(pem)
        return out

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
            except Exception as exc:
                raise ValueError("Failed to verify Metadata signature") from exc

    def parse(self, raw_xml: str) -> ServiceProviderMetadata:
        """Parse raw XML to ServiceProviderMetadata"""

        def _dedupe_keep_order(items: list[str]) -> list[str]:
            seen: set[str] = set()
            out: list[str] = []
            for s in items:
                if s in seen:
                    continue
                seen.add(s)
                out.append(s)
            return out

        root = lxml_from_string(raw_xml.encode())

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

        # Collect every advertised signing/encryption cert as PEMs so the provider can hold them
        # in a keyring. Signing certs include KeyDescriptors with no explicit `use`, which are
        # valid for either purpose.
        signing_pems = _dedupe_keep_order(
            self.get_keydescriptor_cert_pems(root, use="signing")
            + self.get_keydescriptor_cert_pems(root, use=None)
        )
        encryption_pems = _dedupe_keep_order(
            self.get_keydescriptor_cert_pems(root, use="encryption")
        )

        # Verify the metadata signature, if present, against the advertised signing cert.
        signing_keypair = self.get_signing_cert(root)
        if signing_keypair:
            self.check_signature(root, signing_keypair)

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
            name_id_policy=name_id_policy,
            sls_binding=sls_binding,
            sls_location=sls_location,
            signing_cert_pems=signing_pems or None,
            encryption_cert_pems=encryption_pems or None,
        )
