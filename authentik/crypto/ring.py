from dataclasses import dataclass

from authentik.crypto.models import (
    CertificateKeyPair,
    CertificateKeyPairRing,
    CertificateKeyPairRingBinding,
)


@dataclass(frozen=True)
class RingItem:
    keypair: CertificateKeyPair
    order: int


def sync_ring(
    *,
    ring: CertificateKeyPairRing,
    items: list[RingItem],
) -> None:
    """Replace ring membership with `items` (no append semantics)."""
    existing = {b.keypair_id: b for b in ring.bindings.all()}

    desired_ids = set()
    for it in items:
        desired_ids.add(it.keypair.pk)
        b = existing.get(it.keypair.pk)
        if b is None:
            CertificateKeyPairRingBinding.objects.create(
                ring=ring, keypair=it.keypair, order=it.order
            )
        elif b.order != it.order:
            b.order = it.order
            b.save(update_fields=["order"])

    CertificateKeyPairRingBinding.objects.filter(ring=ring).exclude(
        keypair_id__in=desired_ids
    ).delete()

    """KeyPair and Keypair utilities"""


def candidate_cert_pems(
    *,
    kp: CertificateKeyPair | None = None,
    ring: CertificateKeyPairRing | None = None,
) -> list[str]:
    """Return candidate certificate PEMs in try-order (KP wins over ring)."""
    if kp is not None:
        pem = (kp.certificate_data or "").strip()
        return [pem] if pem else []

    if ring is None:
        return []

    bindings = (
        CertificateKeyPairRingBinding.objects.filter(ring=ring)
        .select_related("keypair")
        .order_by("order", "keypair__kp_uuid")
    )

    out: list[str] = []
    for b in bindings:
        pem = (b.keypair.certificate_data or "").strip()
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

    def _from_kp(k: CertificateKeyPair) -> tuple[str | None, str | None]:
        key_pem = (k.key_data or "").strip()
        cert_pem = (k.certificate_data or "").strip()
        if not key_pem:
            return None, None
        return key_pem, cert_pem

    if kp is not None:
        return _from_kp(kp)

    if ring is None:
        return None, None

    bindings = (
        CertificateKeyPairRingBinding.objects.filter(ring=ring)
        .select_related("keypair")
        .order_by("order", "keypair__kp_uuid")
    )
    for b in bindings:
        key_pem, cert_pem = _from_kp(b.keypair)
        if key_pem:
            return key_pem, cert_pem

    return None, None
