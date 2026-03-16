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

/**
 * Determine if the user has conditional webauthn configured for their current device.
 *
 * @remarks
 *
 * Conditional Webauthn is the mechanism where a device can store authentication details and request
 * them automatically on the log-in page; if the user completes the browser-based transaction, their
 * credentials are automatically and completely filled-in, allowing the user to proceed directly to
 * the application.
 *
 * If enabled by site configuration, this controller queries the browser for Webauthn availability
 * and, if present, requests a Webauthn transaction. (On most mobile devices this looks like the OS
 * "pick an identity" and "use biometrics or your pin to unlock the credentials associated with that
 * identity" dialogs.)
 *
 * This has no relationship to the fields presented by IdentificationStage; it is its own routine in
 * filling the data structures otherwise filled by the IdentificationStage and submitting them to
 * the server, so it needs only be added to the host stage and it works automatically.
 *
 * [conditional webauthn](https://developer.chrome.com/docs/identity/webauthn-conditional-ui)
 */
export class WebauthnController implements ReactiveController {
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

export default WebauthnController;
