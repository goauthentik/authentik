import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { WithUserInfoChallenge } from "../../../api/Flows";
import { SpinnerSize } from "../../Spinner";
import { BaseStage } from "../base";
import { Assertion, transformCredentialCreateOptions, transformNewAssertionForServer } from "./utils";

export interface WebAuthnAuthenticatorRegisterChallenge extends WithUserInfoChallenge {
    registration: PublicKeyCredentialCreationOptions;
}

export interface WebAuthnAuthenticatorRegisterChallengeResponse {
    response: Assertion;
}

@customElement("ak-stage-authenticator-webauthn-register")
export class WebAuthnAuthenticatorRegisterStage extends BaseStage {

    @property({ attribute: false })
    challenge?: WebAuthnAuthenticatorRegisterChallenge;

    @property({type: Boolean})
    registerRunning = false;

    @property()
    registerMessage = "";

    createRenderRoot(): Element | ShadowRoot {
        return this;
    }

    async register(): Promise<void> {
        if (!this.challenge) {
            return;
        }
        // convert certain members of the PublicKeyCredentialCreateOptions into
        // byte arrays as expected by the spec.
        const publicKeyCredentialCreateOptions = transformCredentialCreateOptions(this.challenge?.registration);

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
            throw new Error(gettext(`Error creating credential: ${err}`));
        }

        // we now have a new credential! We now need to encode the byte arrays
        // in the credential into strings, for posting to our server.
        const newAssertionForServer = transformNewAssertionForServer(credential);

        // post the transformed credential data to the server for validation
        // and storing the public key
        try {
            const formData = new FormData();
            formData.set("response", JSON.stringify(newAssertionForServer))
            await this.host?.submit(formData);
        } catch (err) {
            throw new Error(gettext(`Server validation of credential failed: ${err}`));
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
                    ${this.challenge?.title}
                </h1>
            </header>
            <div class="pf-c-login__main-body">
                ${this.registerRunning ?
                    html`<div class="pf-c-empty-state__content">
                            <div class="pf-l-bullseye">
                                <div class="pf-l-bullseye__item">
                                    <ak-spinner size="${SpinnerSize.XLarge}"></ak-spinner>
                                </div>
                            </div>
                        </div>`:
                    html`
                    <div class="pf-c-form__group pf-m-action">
                        ${this.challenge?.response_errors ?
                            html`<p class="pf-m-block">${this.challenge.response_errors["response"][0].string}</p>`:
                            html``}
                        <p class="pf-m-block">${this.registerMessage}</p>
                        <button class="pf-c-button pf-m-primary pf-m-block" @click=${() => {
                            this.registerWrapper();
                        }}>
                            ${gettext("Register device")}
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
