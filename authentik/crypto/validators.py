"""Validate that a Certificate-Key Pair's algorithm is usable for a given purpose"""

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

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


def validate_key_type(keypair: CertificateKeyPair | None, allowed: list[KeyType]) -> None:
    """Raise a ValidationError if `keypair` uses a key algorithm not in `allowed`.

    Intended to be called from a `validate_<field>` serializer method, which nests the error under
    that field for us.

    A keypair whose `key_type` is null is rejected rather than allowed through: null means
    `detect_key_type` did not recognize the certificate's public key, so we cannot vouch for it
    being usable, and letting it through is what causes downstream signing to raise instead of
    returning a validation error."""
    if not keypair:
        return
    allowed_labels = ", ".join(str(KeyType(key_type).label) for key_type in allowed)
    if not keypair.key_type:
        raise ValidationError(
            _(
                "Unable to determine the key type of this certificate. Supported key types "
                "are: {allowed}.".format(allowed=allowed_labels)
            )
        )
    if keypair.key_type not in allowed:
        raise ValidationError(
            _(
                "Key type {key_type} is not supported. Supported key types are: {allowed}.".format(
                    key_type=KeyType(keypair.key_type).label,
                    allowed=allowed_labels,
                )
            )
        )
