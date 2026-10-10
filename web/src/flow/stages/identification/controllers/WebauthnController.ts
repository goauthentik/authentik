import {
    isConditionalMediationAvailable,
    transformAssertionForServer,
    transformCredentialRequestOptions,
} from "#common/helpers/webauthn";

import { AKFlowSubmitRequest } from "#flow/events";
import type { IdentificationHost } from "#flow/stages/identification/IdentificationStage";
import { passkeyDebug } from "#flow/stages/identification/passkeyDebug";

import { IdentificationChallenge } from "@goauthentik/api";

import { ReactiveController } from "lit";

// Ask once when the flow interface loads, so the answer is ready before the first challenge.
const conditionalMediationAvailable = isConditionalMediationAvailable().catch((error: unknown) => {
    passkeyDebug("isConditionalMediationAvailable failed", { error: `${error}` });

    return false;
});

passkeyDebug("isConditionalMediationAvailable called");

conditionalMediationAvailable.then((available) =>
    passkeyDebug("isConditionalMediationAvailable resolved", { available }),
);

type PasskeyChallenge = Omit<IdentificationChallenge, "passkeyChallenge"> & {
    passkeyChallenge?: PublicKeyCredentialRequestOptions;
};

/**
 * Determine if the user has conditional webauthn configured for their current device.
 *
 * @remarks
 *
 *   Conditional Webauthn is the mechanism where a device can store authentication details and
 *   request them automatically on the log-in page; if the user completes the browser-based
 *   transaction, their credentials are automatically and completely filled-in, allowing the user to
 *   proceed directly to the application. If enabled by site configuration, this controller queries
 *   the browser for Webauthn availability and, if present, requests a Webauthn transaction. (On
 *   most mobile devices this looks like the OS "pick an identity" and "use biometrics or your pin
 *   to unlock the credentials associated with that identity" dialogs.) This has no relationship to
 *   the fields presented by IdentificationStage; it is its own routine in filling the data
 *   structures otherwise filled by the IdentificationStage and submitting them to the server, so it
 *   needs only be added to the host stage and it works automatically. [conditional
 *   webauthn](https://developer.chrome.com/docs/identity/webauthn-conditional-ui)
 */
export class WebauthnController implements ReactiveController {
    public passkey: PublicKeyCredentialRequestOptions | null = null;

    /**
     * Resolves once the conditional request for the current challenge is pending, or once it is
     * clear there will be none.
     *
     * Safari chooses between password and passkey autofill when the identification field gains
     * focus. If no conditional request is pending at that moment it offers only the saved
     * password, so the host must not focus the field before this resolves.
     */
    public ready: Promise<void> = Promise.resolve();

    constructor(private host: IdentificationHost) {}

    #abortController: AbortController | null = null;

    //#endregion

    get #hostPasskey() {
        return (this.host.challenge as PasskeyChallenge)?.passkeyChallenge ?? null;
    }

    public get live() {
        return !!this.#hostPasskey;
    }

    public hostUpdated() {
        // Only (re)start when the challenge changes; restarting on every re-render would abort
        // the pending request and the passkey autofill dropdown would never appear.
        if (this.passkey !== this.#hostPasskey) {
            this.passkey = this.#hostPasskey;
            passkeyDebug("hostUpdated: challenge changed", { hasPasskey: !!this.passkey });

            if (this.passkey) {
                this.ready = this.#startConditionalWebAuthn(this.passkey).catch((error) => {
                    passkeyDebug("start failed", { error: `${error}` });

                    console.warn("authentik/identification: Conditional WebAuthn failed", error);
                });
            }
        }
    }

    public hostDisconnected() {
        passkeyDebug("hostDisconnected: aborting request", { pending: !!this.#abortController });
        this.#abortController?.abort();
        this.#abortController = null;
    }

    /**
     * Start a conditional WebAuthn request for passkey autofill.
     * This allows users to select a passkey from the browser's autofill dropdown.
     *
     * Resolves as soon as the request is pending, not when the user picks a passkey.
     */
    async #startConditionalWebAuthn(
        passkeyRequestOptions: PublicKeyCredentialRequestOptions,
    ): Promise<void> {
        passkeyDebug("start: waiting for availability");

        if (!(await conditionalMediationAvailable)) {
            passkeyDebug("start: conditional mediation not available");

            console.debug("authentik/identification: Conditional mediation not available");

            return;
        }

        // Abort any existing request
        this.#abortController?.abort();
        this.#abortController = new AbortController();
        const { signal } = this.#abortController;

        const publicKey = transformCredentialRequestOptions(passkeyRequestOptions);

        passkeyDebug("credentials.get called");

        navigator.credentials
            .get({ publicKey, mediation: "conditional", signal })
            .then((credential) => {
                passkeyDebug("credentials.get resolved", { credential: !!credential });

                if (!credential) {
                    console.debug("authentik/identification: No credential returned");

                    return;
                }

                // Transform and submit the passkey response
                const passkey = transformAssertionForServer(credential as PublicKeyCredential);
                this.host.dispatchEvent(new AKFlowSubmitRequest({ passkey }, { invisible: true }));
            })
            .catch((error: unknown) => {
                passkeyDebug("credentials.get rejected", {
                    name: error instanceof Error ? error.name : null,
                    message: `${error}`,
                });

                if (error instanceof Error && error.name === "AbortError") {
                    // Request was aborted, this is expected when navigating away
                    console.debug("authentik/identification: Conditional WebAuthn aborted");

                    return;
                }

                console.warn("authentik/identification: Conditional WebAuthn failed", error);
            });
    }
}

export default WebauthnController;
