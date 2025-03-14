import {
    Assertion,
    checkWebAuthnSupport,
    transformCredentialCreateOptions,
    transformNewAssertionForServer,
} from "@goauthentik/common/helpers/webauthn.js";
import "@goauthentik/elements/EmptyState";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { msg, str } from "@lit/localize";
import { CSSResult, PropertyValues, TemplateResult, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    AuthenticatorWebAuthnChallenge,
    AuthenticatorWebAuthnChallengeResponseRequest,
} from "@goauthentik/api";

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

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFLogin,
            PFFormControl,
            PFForm,
            PFTitle,
            PFButton,
            // FIXME: this is technically duplicate with ../authenticator_validate/base.ts
            css`
                .pf-c-form__group.pf-m-action {
                    display: flex;
                    gap: 16px;
                    margin-top: 0;
                    margin-bottom: calc(var(--pf-c-form__group--m-action--MarginTop) / 2);
                    flex-direction: column;
                }
            `,
        ];
    }

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
            .catch((e) => {
                console.warn("authentik/flows/authenticator_webauthn: failed to register", e);
                this.registerMessage = msg("Failed to register. Please try again.");
            })
            .finally(() => {
                this.registerRunning = false;
            });
    }

    updated(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("challenge") && this.challenge !== undefined) {
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
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${this.challenge?.flowInfo?.title}</h1>
            </header>
            <div class="pf-c-login__main-body">
                <form class="pf-c-form">
                    <ak-form-static
                        class="pf-c-form__group"
                        userAvatar="${this.challenge.pendingUserAvatar}"
                        user=${this.challenge.pendingUser}
                    >
                        <div slot="link">
                            <a href="${ifDefined(this.challenge.flowInfo?.cancelUrl)}"
                                >${msg("Not you?")}</a
                            >
                        </div>
                    </ak-form-static>
                    <ak-empty-state
                        ?loading="${this.registerRunning}"
                        header=${this.registerRunning
                            ? msg("Registering...")
                            : this.registerMessage || msg("Failed to register")}
                        icon="fa-times"
                    >
                    </ak-empty-state>
                    ${this.challenge?.responseErrors
                        ? html`<p class="pf-m-block">
                              ${this.challenge.responseErrors["response"][0].string}
                          </p>`
                        : nothing}
                    <div class="pf-c-form__group pf-m-action">
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
                    </div>
                </form>
            </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-webauthn": WebAuthnAuthenticatorRegisterStage;
    }
}
