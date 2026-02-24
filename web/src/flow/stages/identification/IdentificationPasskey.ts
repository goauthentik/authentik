import { type IdentificationHost } from "./IdentificationStage";

import {
    isConditionalMediationAvailable,
    transformAssertionForServer,
    transformCredentialRequestOptions,
} from "#common/helpers/webauthn";

import { IdentificationChallenge } from "@goauthentik/api";

import { ReactiveController } from "lit";

type PasskeyChallenge = Omit<IdentificationChallenge, "passkeyChallenge"> & {
    passkeyChallenge?: PublicKeyCredentialRequestOptions;
};

export class IdentificationPasskey implements ReactiveController {
    public passkey: PublicKeyCredentialRequestOptions | null = null;

    constructor(private host: IdentificationHost) {}

    #passkeyAbortController: AbortController | null = null;

    //#endregion

    public hostUpdated() {
        if (this.passkey !== (this.host.challenge as PasskeyChallenge)?.passkeyChallenge) {
            this.passkey = (this.host.challenge as PasskeyChallenge)?.passkeyChallenge ?? null;
        }
        if (this.passkey) {
            this.#startConditionalWebAuthn(this.passkey);
        }
    }

    public hostDisconnected() {
        this.#passkeyAbortController?.abort();
        this.#passkeyAbortController = null;
    }

    /**
     * Start a conditional WebAuthn request for passkey autofill.
     * This allows users to select a passkey from the browser's autofill dropdown.
     */
    async #startConditionalWebAuthn(passkey: PublicKeyCredentialRequestOptions): Promise<void> {
        // Check if browser supports conditional mediation
        const isAvailable = await isConditionalMediationAvailable();
        if (!isAvailable) {
            console.debug("authentik/identification: Conditional mediation not available");
            return;
        }

        // Abort any existing request
        this.#passkeyAbortController?.abort();
        this.#passkeyAbortController = new AbortController();

        try {
            const publicKeyOptions = transformCredentialRequestOptions(passkey);

            // Start the conditional WebAuthn request
            const credential = (await navigator.credentials.get({
                publicKey: publicKeyOptions,
                mediation: "conditional",
                signal: this.#passkeyAbortController.signal,
            })) as PublicKeyCredential | null;

            if (!credential) {
                console.debug("authentik/identification: No credential returned");
                return;
            }

            // Transform and submit the passkey response
            const transformedCredential = transformAssertionForServer(credential);

            await this.host.host?.submit(
                {
                    passkey: transformedCredential,
                },
                {
                    invisible: true,
                },
            );
        } catch (error) {
            if (error instanceof Error && error.name === "AbortError") {
                // Request was aborted, this is expected when navigating away
                console.debug("authentik/identification: Conditional WebAuthn aborted");
                return;
            }
            console.warn("authentik/identification: Conditional WebAuthn failed", error);
        }
    }
}
