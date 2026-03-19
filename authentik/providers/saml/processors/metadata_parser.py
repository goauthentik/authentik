"""SAML metadata parser (policy + snapshot/runtime + compatibility DTOs)."""

from dataclasses import dataclass
from typing import Any

import xmlsec
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_pem_x509_certificate
from defusedxml.lxml import fromstring
from lxml import etree  # nosec
from structlog.stdlib import get_logger

from authentik.common.saml.constants import (
    NS_MAP,
)
from authentik.crypto.models import CertificateKeyPair, format_cert
from authentik.flows.models import Flow
from authentik.providers.saml.models import SAMLBindings, SAMLPropertyMapping, SAMLProvider
from authentik.providers.saml.processors import metadata_extract as mx
from authentik.sources.saml.models import SAMLNameIDPolicy

LOGGER = get_logger()

"""Allowed binding tokens for SP ACS/SLS selection."""
_ALLOWED_ACS = {SAMLBindings.POST}  # keep strict for now
_ALLOWED_SLS = {SAMLBindings.POST, SAMLBindings.REDIRECT}

"""Preferred order for selection."""
_PREFER_BINDINGS = (SAMLBindings.POST, SAMLBindings.REDIRECT)
_PREFER_NAME_IDS = {
    SAMLNameIDPolicy.PERSISTENT,
    SAMLNameIDPolicy.TRANSIENT,
    SAMLNameIDPolicy.EMAIL,
    SAMLNameIDPolicy.UNSPECIFIED,
}


def _norm_str(v: Any) -> str:
    if v is None:
        return ""
    return v.strip() if isinstance(v, str) else str(v).strip()


def pick_preferred_service(
    services: Any,
    *,
    allowed_bindings: set[str],
    prefer_order: tuple[str, ...],
) -> dict[str, str] | None:
    """Pick a single endpoint from extracted candidates using allow+prefer policy."""
    if not isinstance(services, list):
        return None

    norm: list[dict[str, str]] = []
    for s in services:
        if not isinstance(s, dict):
            continue
        binding = _norm_str(s.get("binding"))
        url = _norm_str(s.get("url"))
        if not url:
            continue
        if binding not in allowed_bindings:
            continue
        norm.append({"binding": binding, "url": url})

    if not norm:
        return None

    for b in prefer_order:
        for s in norm:
            if s["binding"] == b:
                return s
    return norm[0]


def pick_preferred_name_id_policy(
    name_id_formats: Any,
    *,
    prefer_order: tuple[str, ...] = (
        SAMLNameIDPolicy.PERSISTENT,
        SAMLNameIDPolicy.TRANSIENT,
        SAMLNameIDPolicy.EMAIL,
        SAMLNameIDPolicy.UNSPECIFIED,
    ),
    default: str = SAMLNameIDPolicy.UNSPECIFIED,
) -> str:
    """Pick one NameID policy from a list of NameIDFormat URIs."""
    if not isinstance(name_id_formats, list) or not name_id_formats:
        return default

    # normalize + de-dup stable
    seen: set[str] = set()
    formats: list[str] = []
    for v in name_id_formats:
        s = (v or "").strip()
        if not s or s in seen:
            continue
        formats.append(s)
        seen.add(s)

    # prefer known values
    for p in prefer_order:
        if p in formats:
            return p

    # fallback: use first advertised format
    return formats[0] if formats else default


def build_sp_snapshot(entity: etree._Element) -> dict[str, Any]:
    """Build SP snapshot with stable keys."""
    sp_desc = mx.extract_sp_descriptor(entity)

    acs_list = mx.extract_all_acs(sp_desc)
    sls_list = mx.extract_all_sls(sp_desc)
    name_id_list = mx.extract_nameid_formats(sp_desc)

    verification_b64 = mx.extract_x509_b64_list(sp_desc, use="signing") or mx.extract_x509_b64_list(
        sp_desc, use=None
    )
    encryption_b64 = mx.extract_x509_b64_list(sp_desc, use="encryption")

    return {
        "acs": acs_list,
        "sls": sls_list,
        "name_id_formats": name_id_list,
        "authn_requests_signed": (sp_desc.attrib.get("AuthnRequestsSigned", "").lower() == "true"),
        "want_assertions_signed": (
            sp_desc.attrib.get("WantAssertionsSigned", "").lower() == "true"
        ),
        "has_verification_cert": bool(verification_b64),
        "has_encryption_cert": bool(encryption_b64),
    }


def build_sp_runtime_from_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Deterministically derive SP runtime defaults from snapshot using policy."""
    snap = snapshot or {}

    acs = (
        pick_preferred_service(
            snap.get("acs"),
            allowed_bindings=_ALLOWED_ACS,
            prefer_order=(SAMLBindings.POST,),
        )
        or {}
    )
    sls = (
        pick_preferred_service(
            snap.get("sls"),
            allowed_bindings=_ALLOWED_SLS,
            prefer_order=_PREFER_BINDINGS,
        )
        or {}
    )

    name_id_policy = (
        pick_preferred_name_id_policy(snap.get("name_id_formats"), prefer_order=_PREFER_NAME_IDS)
        or {}
    )

    return {
        "acs_url": (acs.get("url") or "").strip(),
        "sp_binding": (acs.get("binding") or "").strip(),
        "sls_url": (sls.get("url") or "").strip(),
        "sls_binding": (sls.get("binding") or "").strip(),
        "authn_requests_signed": bool(snap.get("authn_requests_signed", False)),
        "want_assertions_signed": bool(snap.get("want_assertions_signed", False)),
        "name_id_policy": name_id_policy.strip(),
    }


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
        """Create a SAMLProvider instance from the details."""
        provider = SAMLProvider.objects.create(
            name=name, authorization_flow=authorization_flow, invalidation_flow=invalidation_flow
        )
        provider.issuer = self.entity_id
        provider.sp_binding = self.acs_binding
        provider.acs_url = self.acs_location
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
        load_pem_x509_certificate(raw_cert.encode("utf-8"), default_backend())
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
        load_pem_x509_certificate(raw_cert.encode("utf-8"), default_backend())
        return CertificateKeyPair(
            certificate_data=raw_cert,
        )

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
        snap = build_sp_snapshot(root)
        runtime = build_sp_runtime_from_snapshot(snap)

        entity_id = root.attrib["entityID"]
        auth_n_request_signed = bool(runtime.get("authn_requests_signed", False))
        assertion_signed = bool(runtime.get("want_assertions_signed", False))
        acs_binding = runtime.get("sp_binding") or SAMLBindings.POST
        acs_location = runtime.get("acs_url") or ""
        signing_keypair = self.get_signing_cert(root)
        """
            WARNING: Signature verification uses KeyInfo cert from the same XML (trust-on-first-use)
            do not treat this as an external trust anchor.
        """
        if signing_keypair:
            self.check_signature(root, signing_keypair)
        encryption_keypair = self.get_encryption_cert(root)

        name_id_policy = runtime.get("name_id_policy") or SAMLNameIDPolicy.UNSPECIFIED
        sls_binding = runtime.get("sls_binding") or None
        sls_location = runtime.get("sls_url") or None

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
