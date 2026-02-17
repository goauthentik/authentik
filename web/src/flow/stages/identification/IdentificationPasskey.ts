import { type IdentificationStage } from "./IdentificationStage";

import {
    isConditionalMediationAvailable,
    transformAssertionForServer,
    transformCredentialRequestOptions,
} from "#common/helpers/webauthn";

import { IdentificationChallenge } from "@goauthentik/api";

import { ReactiveController, type ReactiveControllerHost } from "lit";

type PasskeyChallenge = Omit<IdentificationChallenge, "passkeyChallenge"> & {
    passkeyChallenge?: PublicKeyCredentialRequestOptions;
};

type PasskeyHost = IdentificationStage & ReactiveControllerHost;

export class IdentificationPasskey implements ReactiveController {
    passkey: PublicKeyCredentialRequestOptions | null = null;
    host: IdentificationStage;

    constructor(host: PasskeyHost) {
        this.host = host;
        host.addController(this);
    }

    #passkeyAbortController: AbortController | null = null;

    //#endregion

    hostUpdated() {
        if (this.passkey !== (this.host.challenge as PasskeyChallenge)?.passkeyChallenge) {
            this.passkey = (this.host.challenge as PasskeyChallenge)?.passkeyChallenge ?? null;
        }
        if (this.passkey) {
            this.#startConditionalWebAuthn(this.passkey);
        }
    }

    hostDisconnected() {
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
                }
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
