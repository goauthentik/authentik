import { checkWebAuthnSupport } from "@goauthentik/common/helpers/webauthn";
import "@goauthentik/elements/EmptyState";
import { BaseDeviceStage } from "@goauthentik/flow/stages/authenticator_validate/base";

import { msg } from "@lit/localize";
import { PropertyValues, TemplateResult, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import {
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest,
    DeviceChallenge,
} from "@goauthentik/api";

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
        let assertion: PublicKeyCredential;
        checkWebAuthnSupport();
        try {
            assertion = (await navigator.credentials.get({
                publicKey: this.transformedCredentialRequestOptions,
            })) as PublicKeyCredential;
            if (!assertion) {
                throw new Error("Assertions is empty");
            }
        } catch (err) {
            throw new Error(`Error when creating credential: ${err}`);
        }

        // post the assertion to the server for verification.
        try {
            await this.host?.submit(
                {
                    webauthn: assertion.toJSON(),
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
        if (changedProperties.has("challenge") && this.challenge !== undefined) {
            const credentialRequestOptions = this.deviceChallenge
                ?.challenge as unknown as PublicKeyCredentialRequestOptionsJSON;
            this.transformedCredentialRequestOptions =
                PublicKeyCredential.parseRequestOptionsFromJSON(credentialRequestOptions);
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
        return html`<div class="pf-c-login__main-body">
            <form class="pf-c-form">
                ${this.renderUserInfo()}
                <ak-empty-state ?loading="${this.authenticating}" icon="fa-times">
                    <span
                        >${this.authenticating
                            ? msg("Authenticating...")
                            : this.errorMessage || msg("Loading")}</span
                    >
                </ak-empty-state>
                <div class="pf-c-form__group pf-m-action">
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
                </div>
            </form>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-validate-webauthn": AuthenticatorValidateStageWebAuthn;
    }
}
