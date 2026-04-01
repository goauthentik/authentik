"""SAML metadata parser (policy + snapshot/runtime + compatibility DTOs)."""

from dataclasses import dataclass
from typing import Any

import xmlsec
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_pem_x509_certificate
from defusedxml.lxml import fromstring
from lxml import etree  # nosec
from structlog.stdlib import get_logger

from authentik.common.saml.constants import NS_MAP
from authentik.crypto.models import CertificateKeyPair, CertificateKeyPairRing, format_cert
from authentik.flows.models import Flow
from authentik.providers.saml.processors import metadata_extract as mx
from authentik.providers.saml.processors.metadata_extract import (
    pick_preferred_name_id_policy,
    pick_preferred_service,
)
from authentik.sources.saml.models import SAMLBindingTypes, SAMLNameIDPolicy, SAMLSource

LOGGER = get_logger()

# Allowed binding tokens (normalized by metadata_extract.normalize_binding_uri_to_token)
_ALLOWED_SSO = {"post", "redirect"}
_ALLOWED_SLO = {"post", "redirect"}

_PREFER_BINDINGS = ("post", "redirect")

_PREFER_NAME_IDS = (
    SAMLNameIDPolicy.PERSISTENT,
    SAMLNameIDPolicy.TRANSIENT,
    SAMLNameIDPolicy.EMAIL,
    SAMLNameIDPolicy.UNSPECIFIED,
)

def build_idp_snapshot(entity: etree._Element) -> dict[str, Any]:
    """Build IdP snapshot with stable keys."""
    idp_desc = mx.extract_idp_descriptor(entity)

    sso_list = mx.extract_all_sso(idp_desc)
    slo_list = mx.extract_all_slo(idp_desc)
    name_id_list = mx.extract_nameid_formats(idp_desc)

    verification_b64 = mx.extract_x509_b64_list(idp_desc, use="signing") or mx.extract_x509_b64_list(
        idp_desc, use=None
    )
    encryption_b64 = mx.extract_x509_b64_list(idp_desc, use="encryption")

    return {
        "sso": sso_list,
        "slo": slo_list,
        "name_id_formats": name_id_list,
        # IdPSSODescriptor attribute
        "want_authn_requests_signed": (
            idp_desc.attrib.get("WantAuthnRequestsSigned", "").lower() == "true"
        ),
        "has_verification_cert": bool(verification_b64),
        "has_encryption_cert": bool(encryption_b64),
    }


def build_idp_runtime_from_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Deterministically derive IdP runtime defaults from snapshot using policy."""
    snap = snapshot or {}

    sso = (
        pick_preferred_service(
            snap.get("sso"),
            allowed_bindings=_ALLOWED_SSO,
            prefer_order=_PREFER_BINDINGS,
        )
        or {}
    )
    slo = (
        pick_preferred_service(
            snap.get("slo"),
            allowed_bindings=_ALLOWED_SLO,
            prefer_order=_PREFER_BINDINGS,
        )
        or {}
    )

    name_id_policy = pick_preferred_name_id_policy(
        snap.get("name_id_formats"),
        prefer_order=_PREFER_NAME_IDS,
    )

    return {
        "sso_url": (sso.get("url") or "").strip(),
        "sso_binding": (sso.get("binding") or "").strip(),
        "slo_url": (slo.get("url") or "").strip(),
        "slo_binding": (slo.get("binding") or "").strip(),
        "want_authn_requests_signed": bool(snap.get("want_authn_requests_signed", False)),
        "name_id_policy": (name_id_policy or "").strip(),
    }


@dataclass(slots=True)
class IdentityProviderMetadata:
    """IdP Metadata Dataclass"""

    entity_id: str

    sso_binding: str
    sso_location: str

    want_authn_requests_signed: bool
    name_id_policy: SAMLNameIDPolicy

    """Keys extracted from metadata."""
    signing_cert_pems: list[str] | None = None
    encryption_cert_pems: list[str] | None = None

    # Single Logout Service (optional)
    slo_binding: str | None = None
    slo_location: str | None = None
    def to_source(self, name: str, *, pre_authentication_flow: Flow,issuer: str="") -> SAMLSource:
        """Create a new SAMLSource and apply metadata-derived fields."""
        # NOTE: adjust required fields per your SAMLSource model.
        if name is None:
            raise ValueError("Name is required to create SAMLSource from metadata")
        # kebab-case slug, max length 50 chars
        slug = name.lower().replace(" ", "_")[:50]
        source = SAMLSource.objects.create(
            name=name,
            slug=slug,
            pre_authentication_flow = pre_authentication_flow,
            issuer = issuer,
        )
        self.apply_to_source(source, create_missing_rings=True)
        return source

    def apply_to_source(self, source: SAMLSource, *, create_missing_rings: bool = False) -> None:
        """Apply metadata-derived fields to an existing SAMLSource."""
        # binding_type: normalize token -> enum
        # SAMLBindingTypes enum is different from Binding type options in Provider.
        # Thus, we need to remap from the normalized token to the enum.
        if self.sso_binding == "post":
            source.binding_type = SAMLBindingTypes.POST
        elif self.sso_binding == "redirect":
            source.binding_type = SAMLBindingTypes.REDIRECT

        source.sso_url = self.sso_location
        source.name_id_policy = self.name_id_policy

        # SLO is an optional
        if self.slo_location:
            source.slo_url = self.slo_location

        # ---- verification ring (IdP signing certs) ----
        if self.signing_cert_pems and not source.verification_kp:
            if source.verification_kp_ring is None and create_missing_rings:
                source.verification_kp_ring = CertificateKeyPairRing.objects.create(
                    name=f"Source {source.name} - SAML Verification Ring",
                )
            if source.verification_kp_ring is not None:
                source.verification_kp_ring.sync_membership(
                    [(i, pem) for i, pem in enumerate(self.signing_cert_pems)]
                )

        # encryption certs on IdP are not used by Authentik.

        source.save()

class IdentityProviderMetadataParser:
    """Identity-Provider Metadata Parser"""

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
                "//md:IDPSSODescriptor/md:KeyDescriptor[@use='signing']"
                "//ds:X509Certificate/text()"
            )
        elif use == "encryption":
            xp = (
                "//md:IDPSSODescriptor/md:KeyDescriptor[@use='encryption']"
                "//ds:X509Certificate/text()"
            )
        elif use is None:
            xp = (
                "//md:IDPSSODescriptor/md:KeyDescriptor[not(@use)]"
                "//ds:X509Certificate/text()"
            )
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

    def parse(self, raw_xml: str) -> IdentityProviderMetadata:
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

        snap = build_idp_snapshot(root)
        runtime = build_idp_runtime_from_snapshot(snap)

        signing_pems = self.get_keydescriptor_cert_pems(root, use="signing")
        unspecified_pems = self.get_keydescriptor_cert_pems(root, use=None)
        signing_pems = _dedupe_keep_order(signing_pems + unspecified_pems)

        # Encryption certs on Idp are not used Authentik, but parse it.
        encryption_pems = self.get_keydescriptor_cert_pems(root, use="encryption")
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

        return IdentityProviderMetadata(
            entity_id=root.attrib["entityID"],
            sso_binding=runtime.get("sso_binding") or "redirect",
            sso_location=runtime.get("sso_url") or "",
            want_authn_requests_signed=bool(runtime.get("want_authn_requests_signed", False)),
            name_id_policy=runtime.get("name_id_policy") or SAMLNameIDPolicy.UNSPECIFIED,
            slo_binding=runtime.get("slo_binding") or None,
            slo_location=runtime.get("slo_url") or None,
            signing_cert_pems=signing_pems,
            encryption_cert_pems=encryption_pems,
        )
