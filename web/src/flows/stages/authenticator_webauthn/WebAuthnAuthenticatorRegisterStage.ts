import { t } from "@lingui/macro";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import AKGlobal from "../../../authentik.css";
import { PFSize } from "../../../elements/Spinner";
import { BaseStage } from "../base";
import { Assertion, transformCredentialCreateOptions, transformNewAssertionForServer } from "./utils";
import { AuthenticatorWebAuthnChallenge, AuthenticatorWebAuthnChallengeResponseRequest } from "authentik-api";

export interface WebAuthnAuthenticatorRegisterChallengeResponse {
    response: Assertion;
}

@customElement("ak-stage-authenticator-webauthn")
export class WebAuthnAuthenticatorRegisterStage extends BaseStage<AuthenticatorWebAuthnChallenge, AuthenticatorWebAuthnChallengeResponseRequest> {

    @property({type: Boolean})
    registerRunning = false;

    @property()
    registerMessage = "";

    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFFormControl, PFForm, PFTitle, PFButton, AKGlobal];
    }

    async register(): Promise<void> {
        if (!this.challenge) {
            return;
        }
        // convert certain members of the PublicKeyCredentialCreateOptions into
        // byte arrays as expected by the spec.
        const publicKeyCredentialCreateOptions = transformCredentialCreateOptions(this.challenge?.registration as PublicKeyCredentialCreationOptions);

        // request the authenticator(s) to create a new credential keypair.
        let credential;
        try {
            credential = <PublicKeyCredential> await navigator.credentials.create({
                publicKey: publicKeyCredentialCreateOptions
            });
            if (!credential) {
                throw new Error("Credential is empty");
            }
        } catch (err) {
            throw new Error(t`Error creating credential: ${err}`);
        }

        // we now have a new credential! We now need to encode the byte arrays
        // in the credential into strings, for posting to our server.
        const newAssertionForServer = transformNewAssertionForServer(credential);

        // post the transformed credential data to the server for validation
        // and storing the public key
        try {
            await this.host?.submit({
                response: newAssertionForServer
            });
        } catch (err) {
            throw new Error(t`Server validation of credential failed: ${err}`);
        }
    }

    async registerWrapper(): Promise<void> {
        if (this.registerRunning) {
            return;
        }
        this.registerRunning = true;
        this.register().catch((e) => {
            console.error(e);
            this.registerMessage = e.toString();
        }).finally(() => {
            this.registerRunning = false;
        });
    }

    firstUpdated(): void {
        this.registerWrapper();
    }

    render(): TemplateResult {
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">
                    ${this.challenge?.flowInfo?.title}
                </h1>
            </header>
            <div class="pf-c-login__main-body">
                ${this.registerRunning ?
                    html`<div class="pf-c-empty-state__content">
                            <div class="pf-l-bullseye">
                                <div class="pf-l-bullseye__item">
                                    <ak-spinner size="${PFSize.XLarge}"></ak-spinner>
                                </div>
                            </div>
                        </div>`:
                    html`
                    <div class="pf-c-form__group pf-m-action">
                        ${this.challenge?.responseErrors ?
                            html`<p class="pf-m-block">${this.challenge.responseErrors["response"][0].string}</p>`:
                            html``}
                        <p class="pf-m-block">${this.registerMessage}</p>
                        <button class="pf-c-button pf-m-primary pf-m-block" @click=${() => {
                            this.registerWrapper();
                        }}>
                            ${t`Register device`}
                        </button>
                    </div>`}
            </div>
        </div>
        <footer class="pf-c-login__main-footer">
            <ul class="pf-c-login__main-footer-links">
            </ul>
        </footer>`;
    }

}
