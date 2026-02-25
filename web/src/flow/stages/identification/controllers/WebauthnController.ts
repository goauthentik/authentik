import {
    isConditionalMediationAvailable,
    transformAssertionForServer,
    transformCredentialRequestOptions,
} from "#common/helpers/webauthn";

import { AKFlowSubmitRequest } from "#flow/events";
import type { IdentificationHost } from "#flow/stages/identification/IdentificationStage";

import { IdentificationChallenge } from "@goauthentik/api";

import { ReactiveController } from "lit";

type PasskeyChallenge = Omit<IdentificationChallenge, "passkeyChallenge"> & {
    passkeyChallenge?: PublicKeyCredentialRequestOptions;
};

export class WebauthnIdentificationController implements ReactiveController {
    public passkey: PublicKeyCredentialRequestOptions | null = null;

    constructor(private host: IdentificationHost) {}

    #abortController: AbortController | null = null;

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
        this.#abortController?.abort();
        this.#abortController = null;
    }

    /**
     * Start a conditional WebAuthn request for passkey autofill.
     * This allows users to select a passkey from the browser's autofill dropdown.
     */
    async #startConditionalWebAuthn(
        passkeyRequestOptions: PublicKeyCredentialRequestOptions,
    ): Promise<void> {
        // Check if browser supports conditional mediation
        const isAvailable = await isConditionalMediationAvailable();
        if (!isAvailable) {
            console.debug("authentik/identification: Conditional mediation not available");
            return;
        }

        // Abort any existing request
        this.#abortController?.abort();
        this.#abortController = new AbortController();
        const { signal } = this.#abortController;

        try {
            const publicKey = transformCredentialRequestOptions(passkeyRequestOptions);

            // Start the conditional WebAuthn request
            const credential = (await navigator.credentials.get({
                publicKey,
                mediation: "conditional",
                signal,
            })) as PublicKeyCredential | null;

            if (!credential) {
                console.debug("authentik/identification: No credential returned");
                return;
            }

            // Transform and submit the passkey response
            const passkey = transformAssertionForServer(credential);
            this.host.dispatchEvent(new AKFlowSubmitRequest({ passkey }, { invisible: true }));
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
