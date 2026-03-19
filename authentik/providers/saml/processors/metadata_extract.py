"""SAML metadata XML extractors (no policy): parse, walk, and collect candidates."""

from typing import Any

from lxml import etree  # nosec
from structlog.stdlib import get_logger

from authentik.common.saml.constants import (
    NS_MAP,
    SAML_BINDING_POST,
    SAML_BINDING_REDIRECT,
)

LOGGER = get_logger()


def extract_sp_descriptor(entity: etree._Element) -> etree._Element:
    """Return the first SPSSODescriptor element."""
    sp = entity.xpath("./md:SPSSODescriptor", namespaces=NS_MAP)
    if not sp:
        raise ValueError("EntityDescriptor has no SPSSODescriptor")
    return sp[0]


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
