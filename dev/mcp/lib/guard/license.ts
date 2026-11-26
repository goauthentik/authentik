/**
 * @file Read the claims of an authentik enterprise license, trusting only ones authentik's
 *   licensing CA signed. Mirrors `LicenseKey.validate()` in authentik/enterprise/license.py:
 *   the `x5c` chain must lead to authentik/enterprise/public.pem, and the JWT must verify
 *   against the leaf certificate. Expiry and audience aren't checked: an expired license or one
 *   issued for another install is still evidence of what kind of instance it was issued for.
 */

import { X509Certificate, verify } from "node:crypto";
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { ROOT } from "#dev/lib/git";

export const LICENSING_ROOT = join(ROOT, "authentik", "enterprise", "public.pem");

/**
 * JWT algorithms authentik licenses use, and the hash each one signs with.
 */
const ALGORITHMS: Record<string, string> = { ES384: "sha384", ES512: "sha512" };

export type LicenseCheck =
    | { verified: true; claims: Record<string, unknown> }
    | { verified: false; reason: string };

function decodeJSON(segment: string): Record<string, unknown> {
    const value: unknown = JSON.parse(Buffer.from(segment, "base64url").toString("utf8"));

    if (!value || typeof value !== "object") throw new TypeError("not a JSON object");

    return value as Record<string, unknown>;
}

function issuedBy(cert: X509Certificate, issuer: X509Certificate): boolean {
    return cert.checkIssued(issuer) && cert.verify(issuer.publicKey);
}

export function verifyLicense(
    jwt: string,
    root: Buffer = readFileSync(LICENSING_ROOT),
): LicenseCheck {
    const parts = jwt.trim().split(".");

    if (parts.length !== 3) return { verified: false, reason: "not a JWT" };
    const [headerPart, payloadPart, signaturePart] = parts as [string, string, string];

    let header: Record<string, unknown>;
    let claims: Record<string, unknown>;

    try {
        header = decodeJSON(headerPart);
        claims = decodeJSON(payloadPart);
    } catch {
        return { verified: false, reason: "header or payload isn't valid JSON" };
    }

    const hash = ALGORITHMS[String(header.alg)];

    if (!hash) return { verified: false, reason: `unexpected algorithm ${String(header.alg)}` };

    const x5c = header.x5c;

    if (!Array.isArray(x5c) || x5c.length < 2) {
        return { verified: false, reason: "no certificate chain in the header" };
    }

    let leaf: X509Certificate;
    let intermediate: X509Certificate;

    try {
        leaf = new X509Certificate(Buffer.from(String(x5c[0]), "base64"));
        intermediate = new X509Certificate(Buffer.from(String(x5c[1]), "base64"));

        if (!issuedBy(leaf, intermediate) || !issuedBy(intermediate, new X509Certificate(root))) {
            return {
                verified: false,
                reason: "certificate chain doesn't lead to authentik's licensing CA",
            };
        }
    } catch {
        return { verified: false, reason: "certificate chain can't be parsed" };
    }

    // JWS ECDSA signatures are r||s (IEEE P1363), not DER.
    const signed = verify(
        hash,
        Buffer.from(`${headerPart}.${payloadPart}`),
        { key: leaf.publicKey, dsaEncoding: "ieee-p1363" },
        Buffer.from(signaturePart, "base64url"),
    );

    return signed
        ? { verified: true, claims }
        : { verified: false, reason: "signature doesn't verify" };
}

/** Whether a verified license's claims mark it as issued for development and testing. */
export function isDevTestLicense(check: LicenseCheck): boolean {
    return check.verified && check.claims.dev_test === true;
}
