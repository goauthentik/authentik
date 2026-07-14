"""Validate that a Certificate-Key Pair's algorithm is usable for a given purpose"""

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.utils.representation import smart_repr

from authentik.crypto.models import CertificateKeyPair, KeyType

# Key types that can be signed with via JOSE/JWT. Bounded by JWTAlgorithms.from_private_key, which
# maps RSA to RS256, EC to ES256/384/512, and both Edwards curves to EdDSA (RFC 8037). DSA has no
# JWA signature algorithm at all.
JWT_SIGNING_KEY_TYPES = [KeyType.RSA, KeyType.EC, KeyType.ED25519, KeyType.ED448]

# Key types that can be encrypted to via JOSE/JWE. OAuth2Provider.encrypt hardcodes the
# RSA-OAEP-256 key management algorithm, which has no non-RSA counterpart.
JWE_ENCRYPTION_KEY_TYPES = [KeyType.RSA]

# Key types that have an XML-DSIG signature transform in libxmlsec1.
XML_SIGNING_KEY_TYPES = [KeyType.RSA, KeyType.EC, KeyType.DSA]

# Key types the Go outposts can serve TLS with. Ed448 will never be supported
# See https://github.com/golang/go/issues/29390#issuecomment-614175576
TLS_KEY_TYPES = [KeyType.RSA, KeyType.EC, KeyType.ED25519]


class KeyTypeValidator:
    """Field-level validator that ensures a Certificate-Key Pair uses a key algorithm the
    consuming protocol can actually handle.

    Accepts either a single keypair or a list of them, so it can be attached to both a
    ForeignKey and a ManyToMany field.

    A keypair whose `key_type` is null is rejected rather than allowed through: null means
    `detect_key_type` did not recognize the certificate's public key, so we cannot vouch for it
    being usable, and letting it through is what causes downstream signing to raise instead of
    returning a validation error."""

    allowed: list[KeyType]
    message = _("Key type {key_type} is not supported. Supported key types are: {allowed}.")
    unknown_message = _(
        "Unable to determine the key type of this certificate. "
        "Supported key types are: {allowed}."
    )

    def __init__(self, *allowed: KeyType, message: str | None = None) -> None:
        self.allowed = list(allowed)
        self.message = message or self.message

    def __call__(self, value: CertificateKeyPair | list[CertificateKeyPair] | None):
        keypairs = value if isinstance(value, list) else [value]
        allowed = ", ".join(str(KeyType(key_type).label) for key_type in self.allowed)
        for keypair in keypairs:
            if not keypair:
                continue
            if not keypair.key_type:
                raise ValidationError(self.unknown_message.format(allowed=allowed), code="invalid")
            if keypair.key_type not in self.allowed:
                raise ValidationError(
                    self.message.format(key_type=KeyType(keypair.key_type).label, allowed=allowed),
                    code="invalid",
                )

    def __repr__(self):
        return f"<{self.__class__.__name__}(allowed={smart_repr(self.allowed)})>"
