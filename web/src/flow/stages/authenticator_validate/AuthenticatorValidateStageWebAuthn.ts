import { BaseDeviceStage } from "@goauthentik/app/flow/stages/authenticator_validate/base";
import {
    checkWebAuthnSupport,
    transformAssertionForServer,
    transformCredentialRequestOptions,
} from "@goauthentik/common/helpers/webauthn";
import "@goauthentik/elements/EmptyState";
import { AuthenticatorValidateStage } from "@goauthentik/flow/stages/authenticator_validate/AuthenticatorValidateStage";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { WebAuthnDeviceChallenge, WebAuthnDeviceChallengeResponseRequest } from "@goauthentik/api";

@customElement("ak-stage-authenticator-validate-webauthn")
export class AuthenticatorValidateStageWebAuthn extends BaseDeviceStage<
    WebAuthnDeviceChallenge,
    WebAuthnDeviceChallengeResponseRequest
> {
    @property()
    authenticateMessage?: string;

    @state()
    authenticating = false;

    transformedCredentialRequestOptions?: PublicKeyCredentialRequestOptions;

    static get styles(): CSSResult[] {
        return super.styles.concat(css``);
    }

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
                throw new Error(msg("Assertions is empty"));
            }
        } catch (err) {
            throw new Error(msg(str`Error when creating credential: ${err}`));
        }

        // we now have an authentication assertion! encode the byte arrays contained
        // in the assertion data as strings for posting to the server
        const transformedAssertionForServer = transformAssertionForServer(
            assertion as PublicKeyCredential,
        );

        // post the assertion to the server for verification.
        try {
            await this.submitDeviceChallenge({
                data: transformedAssertionForServer,
                uid: this.deviceChallenge?.uid || "",
            });
        } catch (err) {
            throw new Error(msg(str`Error when validating assertion on server: ${err}`));
        }
    }

    firstUpdated(): void {
        // convert certain members of the PublicKeyCredentialRequestOptions into
        // byte arrays as expected by the spec.
        const credentialRequestOptions = this.deviceChallenge
            ?.data as PublicKeyCredentialRequestOptions;
        this.transformedCredentialRequestOptions =
            transformCredentialRequestOptions(credentialRequestOptions);
        this.authenticateWrapper();
    }

    async authenticateWrapper(): Promise<void> {
        if (this.authenticating) {
            return;
        }
        this.authenticateMessage = undefined;
        this.authenticating = true;
        this.authenticate()
            .catch((e) => {
                console.error(e);
                this.authenticateMessage = e.toString();
            })
            .finally(() => {
                this.authenticating = false;
            });
    }

    render(): TemplateResult {
        if (this.authenticating) {
            return html`<ak-empty-state ?loading=${true} header=${msg("Loading")}>
                          </ak-empty-state>`;
        }
        return html`<div class="pf-c-login__main-body">
                ${this.authenticateMessage
                    ? html`<div class="pf-c-form__group pf-m-action">
                              <p class="pf-m-block">${this.authenticateMessage}</p>
                          </div>
                          <div class="pf-c-form__group pf-m-action">
                              <button
                                  class="pf-c-button pf-m-primary pf-m-block"
                                  @click=${() => {
                                      this.authenticateWrapper();
                                  }}
                              >
                                  ${msg("Retry authentication")}
                              </button>
                              ${this.showBackButton
                                  ? html`<button
                                        class="pf-c-button pf-m-secondary pf-m-block"
                                        @click=${() => {
                                            if (!this.host) return;
                                            (
                                                this.host as AuthenticatorValidateStage
                                            ).selectedDeviceChallenge = undefined;
                                        }}
                                    >
                                        ${msg("Return to device picker")}
                                    </button>`
                                  : nothing}
                          </div>

            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`
                    : nothing}
            </div>`;
    }
}
