import "#elements/EmptyState";
import "#flow/components/ak-flow-card";
import "#flow/FormStatic";

import {
    Assertion,
    checkWebAuthnSupport,
    transformCredentialCreateOptions,
    transformNewAssertionForServer,
} from "#common/helpers/webauthn";

import { FlowUserDetails } from "#flow/FormStatic";
import { BaseStage } from "#flow/stages/base";

import {
    AuthenticatorWebAuthnChallenge,
    AuthenticatorWebAuthnChallengeResponseRequest,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

export interface WebAuthnAuthenticatorRegisterChallengeResponse {
    response: Assertion;
}

@customElement("ak-stage-authenticator-webauthn")
export class WebAuthnAuthenticatorRegisterStage extends BaseStage<
    AuthenticatorWebAuthnChallenge,
    AuthenticatorWebAuthnChallengeResponseRequest
> {
    @property({ type: Boolean })
    registerRunning = false;

    @property()
    registerMessage = "";

    publicKeyCredentialCreateOptions?: PublicKeyCredentialCreationOptions;

    static styles: CSSResult[] = [PFLogin, PFFormControl, PFForm, PFTitle, PFButton];

    async register(): Promise<void> {
        if (!this.challenge) {
            return;
        }
        checkWebAuthnSupport();
        // request the authenticator(s) to create a new credential keypair.
        let credential;
        try {
            credential = (await navigator.credentials.create({
                publicKey: this.publicKeyCredentialCreateOptions,
            })) as PublicKeyCredential;
            if (!credential) {
                throw new Error("Credential is empty");
            }
        } catch (err) {
            throw new Error(msg(str`Error creating credential: ${err}`));
        }

        // we now have a new credential! We now need to encode the byte arrays
        // in the credential into strings, for posting to our server.
        const newAssertionForServer = transformNewAssertionForServer(credential);

        // post the transformed credential data to the server for validation
        // and storing the public key
        try {
            await this.host?.submit(
                {
                    response: newAssertionForServer,
                },
                {
                    invisible: true,
                },
            );
        } catch (err) {
            throw new Error(msg(str`Server validation of credential failed: ${err}`));
        }
    }

    async registerWrapper(): Promise<void> {
        if (this.registerRunning) {
            return;
        }
        this.registerRunning = true;
        this.register()
            .catch((error: unknown) => {
                console.warn("authentik/flows/authenticator_webauthn: failed to register", error);

                this.registerMessage = msg("Failed to register. Please try again.");
            })
            .finally(() => {
                this.registerRunning = false;
            });
    }

    updated(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("challenge") && this.challenge) {
            // convert certain members of the PublicKeyCredentialCreateOptions into
            // byte arrays as expected by the spec.
            this.publicKeyCredentialCreateOptions = transformCredentialCreateOptions(
                this.challenge?.registration as PublicKeyCredentialCreationOptions,
                this.challenge?.registration.user.id,
            );
            this.registerWrapper();
        }
    }

    render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form">
                ${FlowUserDetails({ challenge: this.challenge })}

                <ak-empty-state ?loading="${this.registerRunning}" icon="fa-times">
                    <span
                        >${this.registerRunning
                            ? msg("Registering...")
                            : this.registerMessage || msg("Failed to register")}
                    </span>
                </ak-empty-state>
                ${this.challenge?.responseErrors
                    ? html`<p>${this.challenge.responseErrors.response[0].string}</p>`
                    : nothing}
                <fieldset class="pf-c-form__group pf-m-action">
                    <legend class="sr-only">${msg("Form actions")}</legend>
                    ${!this.registerRunning
                        ? html` <button
                              class="pf-c-button pf-m-primary pf-m-block"
                              @click=${() => {
                                  this.registerWrapper();
                              }}
                              type="button"
                          >
                              ${msg("Retry registration")}
                          </button>`
                        : nothing}
                </fieldset>
            </form>
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-webauthn": WebAuthnAuthenticatorRegisterStage;
    }
}
