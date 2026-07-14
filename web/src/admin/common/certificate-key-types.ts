import { KeyTypeEnum } from "@goauthentik/api";

/**
 * Key algorithms accepted for each certificate purpose.
 *
 * These mirror the allowlists enforced server-side in `authentik/crypto/validators.py`. They are
 * duplicated here only so the certificate pickers can filter out keypairs that would be rejected;
 * the server remains the source of truth.
 */

/** Signing a JWT. Bounded by the algorithms `JWTAlgorithms.from_private_key` can map to. */
export const JWTSigningKeyTypes = [
    KeyTypeEnum.Rsa,
    KeyTypeEnum.Ec,
    KeyTypeEnum.Ed25519,
    KeyTypeEnum.Ed448,
];

/** Encrypting a JWT. `RSA-OAEP-256` is hardcoded, and has no non-RSA counterpart. */
export const JWEEncryptionKeyTypes = [KeyTypeEnum.Rsa];

/** Signing XML. Bounded by the signature transforms libxmlsec1 provides. */
export const XMLSigningKeyTypes = [KeyTypeEnum.Rsa, KeyTypeEnum.Ec, KeyTypeEnum.Dsa];

/** Serving TLS. Bounded by what Go's `crypto/tls` can build a certificate from. */
export const TLSKeyTypes = [KeyTypeEnum.Rsa, KeyTypeEnum.Ec, KeyTypeEnum.Ed25519];
