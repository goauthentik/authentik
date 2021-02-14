import { gettext } from "django";
import { customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { SpinnerSize } from "../../Spinner";
import { getCredentialCreateOptionsFromServer, postNewAssertionToServer, transformCredentialCreateOptions, transformNewAssertionForServer } from "./utils";

@customElement("ak-stage-webauthn-register")
export class WebAuthnRegister extends LitElement {

    @property({type: Boolean})
    registerRunning = false;

    createRenderRoot(): Element | ShadowRoot {
        return this;
    }

    async register(): Promise<void> {
        // post the data to the server to generate the PublicKeyCredentialCreateOptions
        let credentialCreateOptionsFromServer;
        try {
            credentialCreateOptionsFromServer = await getCredentialCreateOptionsFromServer();
        } catch (err) {
            throw new Error(gettext(`Failed to generate credential request options: ${err}`));
        }

        // convert certain members of the PublicKeyCredentialCreateOptions into
        // byte arrays as expected by the spec.
        const publicKeyCredentialCreateOptions = transformCredentialCreateOptions(credentialCreateOptionsFromServer);

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
            await postNewAssertionToServer(newAssertionForServer);
        } catch (err) {
            throw new Error(gettext(`Server validation of credential failed: ${err}`));
        }
        this.finishStage();
    }

    async registerWrapper(): Promise<void> {
        if (this.registerRunning) {
            return;
        }
        this.registerRunning = true;
        this.register().finally(() => {
            this.registerRunning = false;
        });
    }

    finishStage(): void {
        // Mark this stage as done
        const confirmationForm = document.querySelector<HTMLFormElement>("form#stage-confirmation");
        if (!confirmationForm) {
            return;
        }
        confirmationForm.submit();
    }

    firstUpdated(): void {
        this.registerWrapper();
    }

    render(): TemplateResult {
        return this.registerRunning ?
            html`<div class="pf-c-empty-state pf-m-full-height">
                <div class="pf-c-empty-state__content">
                    <div class="pf-l-bullseye">
                        <div class="pf-l-bullseye__item">
                            <ak-spinner size="${SpinnerSize.XLarge}"></ak-spinner>
                        </div>
                    </div>
                </div>
            </div>`:
            html`
            <div class="pf-c-form__group pf-m-action">
                <button class="pf-c-button pf-m-primary pf-m-block" @click=${() => {
                    this.registerWrapper();
                }}>
                    ${gettext("Register device")}
                </button>&nbsp;
                <button class="pf-c-button pf-m-secondary pf-m-block" @click=${() => {
                    this.finishStage();
                }}>
                    ${gettext("Skip")}
                </button>
            </div>`;
    }

}
