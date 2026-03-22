"""KeyPair and KeyPairRing utilities.

Policy:
- KP wins over ring.
- Ring ordering is (order, keypair.kp_uuid) for stability.
- Core helpers return CertificateKeyPair objects (not PEM).
"""

from __future__ import annotations

from authentik.crypto.models import (
    CertificateKeyPair,
    CertificateKeyPairRing,
    CertificateKeyPairRingBinding,
)


def _candidate_keypairs(
    *,
    kp: CertificateKeyPair | None = None,
    ring: CertificateKeyPairRing | None = None,
) -> list[CertificateKeyPair]:
    """Return candidate CertificateKeyPair objects in try-order (KP wins over ring)."""
    if kp is not None:
        # even if cert/key is empty, caller can decide; keep behavior predictable
        return [kp]

    if ring is None:
        return []

    bindings = (
        CertificateKeyPairRingBinding.objects.filter(ring=ring)
        .select_related("keypair")
        .order_by("order", "keypair__kp_uuid")
    )
    return [b.keypair for b in bindings]


def candidate_cert_pems(
    *,
    kp: CertificateKeyPair | None = None,
    ring: CertificateKeyPairRing | None = None,
) -> list[str]:
    """Return candidate certificate PEMs in try-order (KP wins over ring)."""
    out: list[str] = []
    for k in _candidate_keypairs(kp=kp, ring=ring):
        pem = (k.certificate_data or "").strip()
        if pem:
            out.append(pem)
    return out


def pick_cert_pem(
    *,
    kp: CertificateKeyPair | None = None,
    ring: CertificateKeyPairRing | None = None,
) -> str | None:
    """Pick most preferred cert PEM (first item from candidate_cert_pems)."""
    pems = candidate_cert_pems(kp=kp, ring=ring)
    return pems[0] if pems else None


def pick_private_key_pem(
    *,
    kp: CertificateKeyPair | None = None,
    ring: CertificateKeyPairRing | None = None,
) -> tuple[str | None, str | None]:
    """Pick (private_key_pem, cert_pem) in try-order (KP wins over ring)."""
    for k in _candidate_keypairs(kp=kp, ring=ring):
        key_pem = (k.key_data or "").strip()
        if not key_pem:
            continue
        cert_pem = (k.certificate_data or "").strip()
        return key_pem, cert_pem
    return None, None
