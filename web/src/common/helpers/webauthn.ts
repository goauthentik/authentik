import { msg } from "@lit/localize";

export function checkWebAuthnSupport() {
    if ("credentials" in navigator) {
        return;
    }
    if (window.location.protocol === "http:" && window.location.hostname !== "localhost") {
        throw new Error(msg("WebAuthn requires this page to be accessed via HTTPS."));
    }
    throw new Error(msg("WebAuthn not supported by browser."));
}
