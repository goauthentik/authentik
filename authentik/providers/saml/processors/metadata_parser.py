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
from authentik.crypto.models import (
    CertificateKeyPair,
    CertificateKeyPairRing,
    format_cert,
)
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
_PREFER_NAME_IDS = (
    SAMLNameIDPolicy.PERSISTENT,
    SAMLNameIDPolicy.TRANSIENT,
    SAMLNameIDPolicy.EMAIL,
    SAMLNameIDPolicy.UNSPECIFIED,
)


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
    prefer_order: tuple[str, ...] = _PREFER_NAME_IDS,
    default: str = SAMLNameIDPolicy.UNSPECIFIED,
) -> str:
    """Pick one NameID policy from a list of NameIDFormat URIs."""
    if not isinstance(name_id_formats, list) or not name_id_formats:
        return default

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

    name_id_policy = pick_preferred_name_id_policy(
        snap.get("name_id_formats"), prefer_order=_PREFER_NAME_IDS
    )

    return {
        "acs_url": (acs.get("url") or "").strip(),
        "sp_binding": (acs.get("binding") or "").strip(),
        "sls_url": (sls.get("url") or "").strip(),
        "sls_binding": (sls.get("binding") or "").strip(),
        "authn_requests_signed": bool(snap.get("authn_requests_signed", False)),
        "want_assertions_signed": bool(snap.get("want_assertions_signed", False)),
        "name_id_policy": (name_id_policy or "").strip(),
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

    """Keys extracted from metadata."""
    signing_cert_pems: list[str] | None = None
    encryption_cert_pems: list[str] | None = None

    # Single Logout Service (optional)
    sls_binding: str | None = None
    sls_location: str | None = None

    def to_provider(
        self, name: str, authorization_flow: Flow, invalidation_flow: Flow
    ) -> SAMLProvider:
        """Create a new SAMLProvider and apply metadata-derived fields."""
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
        """Apply metadata-derived fields to an existing SAMLProvider."""
        provider.issuer = self.entity_id
        provider.sp_binding = self.acs_binding
        provider.acs_url = self.acs_location
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
        """Optional external certificate used to verify ds:Signature (do not trust KeyInfo)."""
        self.signing_certificate = signing_certificate

    def get_keydescriptor_cert_pems(
        self,
        root: etree.Element,
        *,
        use: str | None,
    ) -> list[str]:
        if use == "signing":
            xp = (
                "//md:SPSSODescriptor/md:KeyDescriptor[@use='signing']"
                "//ds:X509Certificate/text()"
            )
        elif use == "encryption":
            xp = (
                "//md:SPSSODescriptor/md:KeyDescriptor[@use='encryption']"
                "//ds:X509Certificate/text()"
            )
        elif use is None:
            xp = "//md:SPSSODescriptor/md:KeyDescriptor[not(@use)]" "//ds:X509Certificate/text()"
        else:
            raise ValueError("Invalid use")

        out: list[str] = []
        for b64 in root.xpath(xp, namespaces=NS_MAP):
            pem = format_cert(b64).strip()
            load_pem_x509_certificate(pem.encode("utf-8"), default_backend())  # sanity check
            out.append(pem)
        return out

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
        def _dedupe_keep_order(items: list[str]) -> list[str]:
            seen: set[str] = set()
            out: list[str] = []
            for s in items:
                if s in seen:
                    continue
                seen.add(s)
                out.append(s)
            return out

        root = fromstring(raw_xml.encode())

        snap = build_sp_snapshot(root)
        runtime = build_sp_runtime_from_snapshot(snap)

        signing_pems = self.get_keydescriptor_cert_pems(root, use="signing")
        unspecified_pems = self.get_keydescriptor_cert_pems(root, use=None)
        encryption_pems = self.get_keydescriptor_cert_pems(root, use="encryption")

        signing_pems = _dedupe_keep_order(signing_pems + unspecified_pems)
        encryption_pems = _dedupe_keep_order(encryption_pems)

        sig_nodes = root.xpath("/md:EntityDescriptor/ds:Signature", namespaces=NS_MAP)
        if len(sig_nodes) == 1:
            if self.signing_certificate is not None:
                self.check_signature(root, self.signing_certificate)  # external anchor
            else:
                """WARNING (TOFU): Verifying with an embedded certificate is not a trust anchor."""
                if not signing_pems:
                    raise ValueError("Metadata is signed but no signing certificate is present")
                last_exc: Exception | None = None
                for pem in signing_pems:
                    try:
                        self.check_signature(root, CertificateKeyPair(certificate_data=pem))
                        break
                    except ValueError as exc:
                        last_exc = exc
                else:
                    raise last_exc or ValueError("Failed to verify Metadata signature")

        return ServiceProviderMetadata(
            entity_id=root.attrib["entityID"],
            acs_binding=runtime.get("sp_binding") or SAMLBindings.POST,
            acs_location=runtime.get("acs_url") or "",
            auth_n_request_signed=bool(runtime.get("authn_requests_signed", False)),
            assertion_signed=bool(runtime.get("want_assertions_signed", False)),
            name_id_policy=runtime.get("name_id_policy") or SAMLNameIDPolicy.UNSPECIFIED,
            sls_binding=runtime.get("sls_binding") or None,
            sls_location=runtime.get("sls_url") or None,
            signing_cert_pems=signing_pems,
            encryption_cert_pems=encryption_pems,
        )
