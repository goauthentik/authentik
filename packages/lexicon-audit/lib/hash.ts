import { createHash } from "node:crypto";

/**
 * Hex-encoded SHA-256 digest.
 */
export function sha256(value: string | Uint8Array): string {
    return createHash("sha256").update(value).digest("hex");
}
