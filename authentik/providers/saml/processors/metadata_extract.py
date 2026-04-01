"""SAML metadata XML extractors (no policy): parse, walk, and collect candidates."""

from typing import Any

from lxml import etree  # nosec
from structlog.stdlib import get_logger

from authentik.common.saml.constants import (
    NS_MAP,
    SAML_BINDING_POST,
    SAML_BINDING_REDIRECT,
)
from authentik.sources.saml.models import SAMLNameIDPolicy

_PREFER_NAME_IDS = (
    SAMLNameIDPolicy.PERSISTENT,
    SAMLNameIDPolicy.TRANSIENT,
    SAMLNameIDPolicy.EMAIL,
    SAMLNameIDPolicy.UNSPECIFIED,
)

LOGGER = get_logger()

def extract_sp_descriptor(entity: etree._Element) -> etree._Element:
    """Return the first SPSSODescriptor element."""
    sp = entity.xpath("./md:SPSSODescriptor", namespaces=NS_MAP)
    if not sp:
        raise ValueError("EntityDescriptor has no SPSSODescriptor")
    return sp[0]

def extract_idp_descriptor(entity: etree._Element) -> etree._Element:
    """Return the first IDPSSODescriptor element."""
    idp = entity.xpath("./md:IDPSSODescriptor", namespaces=NS_MAP)
    if not idp:
        raise ValueError("EntityDescriptor has no IDPSSODescriptor")
    return idp[0]

# ============================================================
# Candidate extraction
# ============================================================


def normalize_binding_uri_to_token(binding_uri: str) -> str:
    """Convert binding URI to a short token if recognizable; otherwise return input."""
    # keep this as "normalization", not "policy"
    if binding_uri == SAML_BINDING_POST:
        return "post"
    if "HTTP-Redirect" in SAML_BINDING_REDIRECT:
        return "redirect"
    return binding_uri


def _extract_all_candidates(desc: etree._Element, element_xpath: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for n in desc.xpath(element_xpath, namespaces=NS_MAP):
        url = (n.attrib.get("Location") or "").strip()
        binding_uri = (n.attrib.get("Binding") or "").strip()
        if not url or not binding_uri:
            continue
        binding = normalize_binding_uri_to_token(binding_uri)
        index = int(n.attrib.get("index", 0))
        results.append({"url": url, "binding": binding, "index": index})
    results.sort(key=lambda x: x["index"])
    return results

def extract_all_acs(sp_desc: etree._Element) -> list[dict[str, Any]]:
    """Extract all AssertionConsumerService endpoints (normalized binding token)."""
    return _extract_all_candidates(sp_desc, "./md:AssertionConsumerService")


def extract_all_sls(sp_desc: etree._Element) -> list[dict[str, Any]]:
    """Extract all SingleLogoutService endpoints (normalized binding token)."""
    return _extract_all_candidates(sp_desc, "./md:SingleLogoutService")


def extract_all_sso(idp_desc: etree._Element) -> list[dict[str, Any]]:
    """Extract all SingleSignOnService endpoints (normalized binding token)."""
    return _extract_all_candidates(idp_desc, "./md:SingleSignOnService")


def extract_all_slo(idp_desc: etree._Element) -> list[dict[str, Any]]:
    """Extract all SingleLogoutService endpoints (normalized binding token)."""
    return _extract_all_candidates(idp_desc, "./md:SingleLogoutService")


def extract_nameid_formats(desc: etree._Element) -> list[str]:
    """Extract NameIDFormat texts (dedup stable)."""
    vals: list[str] = []
    for el in desc.xpath("./md:NameIDFormat", namespaces=NS_MAP):
        if el.text and el.text.strip():
            vals.append(el.text.strip())
    seen: set[str] = set()
    out: list[str] = []
    for v in vals:
        if v not in seen:
            out.append(v)
            seen.add(v)
    return out


def extract_x509_b64_list(
    descriptor: etree._Element,
    *,
    use: str | None = None,
) -> list[str]:
    """Extract X509Certificate values from KeyDescriptor, optionally filtered by @use."""
    if use == "signing":
        xp = "./md:KeyDescriptor[@use='signing']//ds:X509Certificate"
    elif use == "encryption":
        xp = "./md:KeyDescriptor[@use='encryption']//ds:X509Certificate"
    elif use is None:
        xp = "./md:KeyDescriptor[not(@use)]//ds:X509Certificate"
    else:
        raise ValueError("Invalid use value")

    out: list[str] = []
    seen: set[str] = set()
    for n in descriptor.xpath(xp, namespaces=NS_MAP):
        txt = (n.text or "").strip()
        if txt and txt not in seen:
            out.append(txt)
            seen.add(txt)
    return out

def norm_str(v: Any) -> str:
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
        binding = norm_str(s.get("binding"))
        url = norm_str(s.get("url"))
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

    for p in prefer_order:
        if p in formats:
            return p

    return formats[0] if formats else default
