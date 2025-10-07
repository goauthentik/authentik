import "#elements/EmptyState";

import {
    checkWebAuthnSupport,
    transformAssertionForServer,
    transformCredentialRequestOptions,
} from "#common/helpers/webauthn";

import { BaseDeviceStage } from "#flow/stages/authenticator_validate/base";

import {
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest,
    DeviceChallenge,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

@customElement("ak-stage-authenticator-validate-webauthn")
export class AuthenticatorValidateStageWebAuthn extends BaseDeviceStage<
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest
> {
    @property({ attribute: false })
    deviceChallenge?: DeviceChallenge;

    @property()
    errorMessage?: string;

    @property({ type: Boolean })
    showBackButton = false;

    @state()
    authenticating = false;

    transformedCredentialRequestOptions?: PublicKeyCredentialRequestOptions;

    async authenticate(): Promise<void> {
        // request the authenticator to create an assertion signature using the
        // credential private key
        let assertion;
        checkWebAuthnSupport();
        try {
            assertion = await navigator.credentials.get({
                publicKey: this.transformedCredentialRequestOptions,
            });
            if (!assertion) {
                throw new Error("Assertions is empty");
            }
        } catch (err) {
            throw new Error(`Error when creating credential: ${err}`);
        }

        // we now have an authentication assertion! encode the byte arrays contained
        // in the assertion data as strings for posting to the server
        const transformedAssertionForServer = transformAssertionForServer(
            assertion as PublicKeyCredential,
        );

        // post the assertion to the server for verification.
        try {
            await this.host?.submit(
                {
                    webauthn: transformedAssertionForServer,
                },
                {
                    invisible: true,
                },
            );
        } catch (err) {
            throw new Error(`Error when validating assertion on server: ${err}`);
        }
    }

    updated(changedProperties: PropertyValues<this>) {
        super.updated(changedProperties);

        if (changedProperties.has("challenge") && this.challenge !== undefined) {
            // convert certain members of the PublicKeyCredentialRequestOptions into
            // byte arrays as expected by the spec.
            const credentialRequestOptions = this.deviceChallenge
                ?.challenge as PublicKeyCredentialRequestOptions;
            this.transformedCredentialRequestOptions =
                transformCredentialRequestOptions(credentialRequestOptions);
            this.authenticateWrapper();
        }
    }

    async authenticateWrapper(): Promise<void> {
        if (this.authenticating) {
            return;
        }
        this.authenticating = true;
        this.authenticate()
            .catch((error: unknown) => {
                console.warn(
                    "authentik/flows/authenticator_validate/webauthn: failed to auth",
                    error,
                );
                this.errorMessage = msg("Authentication failed. Please try again.");
            })
            .finally(() => {
                this.authenticating = false;
            });
    }

    render(): TemplateResult {
        return html` <form class="pf-c-form">
            ${this.renderUserInfo()}
            <ak-empty-state ?loading="${this.authenticating}" icon="fa-times">
                <span
                    >${this.authenticating
                        ? msg("Authenticating...")
                        : this.errorMessage || msg("Loading")}</span
                >
            </ak-empty-state>
            ${!this.authenticating || this.showBackButton
                ? html`<fieldset class="pf-c-form__group pf-m-action">
                      <legend class="sr-only">${msg("Form actions")}</legend>
                      ${!this.authenticating
                          ? html` <button
                                class="pf-c-button pf-m-primary pf-m-block"
                                @click=${() => {
                                    this.authenticateWrapper();
                                }}
                                type="button"
                            >
                                ${msg("Retry authentication")}
                            </button>`
                          : nothing}
                      ${this.renderReturnToDevicePicker()}
                  </fieldset>`
                : nothing}
        </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-validate-webauthn": AuthenticatorValidateStageWebAuthn;
    }
}
