import {
    Assertion,
    checkWebAuthnSupport,
    transformCredentialCreateOptions,
    transformNewAssertionForServer,
} from "@goauthentik/common/helpers/webauthn";
import { PFSize } from "@goauthentik/elements/Spinner";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

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
        return [PFBase, PFLogin, PFFormControl, PFForm, PFTitle, PFButton];
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
            await this.host?.submit({
                response: newAssertionForServer,
            });
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
                console.error(e);
                this.registerMessage = e.toString();
            })
            .finally(() => {
                this.registerRunning = false;
            });
    }

    firstUpdated(): void {
        // convert certain members of the PublicKeyCredentialCreateOptions into
        // byte arrays as expected by the spec.
        this.publicKeyCredentialCreateOptions = transformCredentialCreateOptions(
            this.challenge?.registration as PublicKeyCredentialCreationOptions,
            this.challenge?.registration.user.id,
        );
        this.registerWrapper();
    }

    render(): TemplateResult {
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">
                    ${this.challenge?.flowInfo?.title}
                </h1>
            </header>
            <div class="pf-c-login__main-body">
                ${
                    this.registerRunning
                        ? html`<div class="pf-c-empty-state__content">
                              <div class="pf-l-bullseye">
                                  <div class="pf-l-bullseye__item">
                                      <ak-spinner size="${PFSize.XLarge}"></ak-spinner>
                                  </div>
                              </div>
                          </div>`
                        : html` <div class="pf-c-form__group pf-m-action">
                              ${this.challenge?.responseErrors
                                  ? html`<p class="pf-m-block">
                                        ${this.challenge.responseErrors["response"][0].string}
                                    </p>`
                                  : html``}
                              <p class="pf-m-block">${this.registerMessage}</p>
                              <button
                                  class="pf-c-button pf-m-primary pf-m-block"
                                  @click=${() => {
                                      this.registerWrapper();
                                  }}
                              >
                                  ${msg("Register device")}
                              </button>
                          </div>`
                }
            </div>
        </div>
        <footer class="pf-c-login__main-footer">
            <ul class="pf-c-login__main-footer-links">
            </ul>
        </footer>`;
    }
}
