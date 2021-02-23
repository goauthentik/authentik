import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { SpinnerSize } from "../../Spinner";
import { transformAssertionForServer, transformCredentialRequestOptions } from "../authenticator_webauthn/utils";
import { BaseStage } from "../base";
import { AuthenticatorValidateStageChallenge, DeviceChallenge } from "./AuthenticatorValidateStage";

@customElement("ak-stage-authenticator-validate-webauthn")
export class AuthenticatorValidateStageWebAuthn extends BaseStage {

    @property({attribute: false})
    challenge?: AuthenticatorValidateStageChallenge;

    @property({attribute: false})
    deviceChallenge?: DeviceChallenge;

    @property({ type: Boolean })
    authenticateRunning = false;

    @property()
    authenticateMessage = "";

    async authenticate(): Promise<void> {
        // convert certain members of the PublicKeyCredentialRequestOptions into
        // byte arrays as expected by the spec.
        const credentialRequestOptions = <PublicKeyCredentialRequestOptions>this.deviceChallenge?.challenge;
        const transformedCredentialRequestOptions = transformCredentialRequestOptions(credentialRequestOptions);

        // request the authenticator to create an assertion signature using the
        // credential private key
        let assertion;
        try {
            assertion = await navigator.credentials.get({
                publicKey: transformedCredentialRequestOptions,
            });
            if (!assertion) {
                throw new Error(gettext("Assertions is empty"));
            }
        } catch (err) {
            throw new Error(gettext(`Error when creating credential: ${err}`));
        }

        // we now have an authentication assertion! encode the byte arrays contained
        // in the assertion data as strings for posting to the server
        const transformedAssertionForServer = transformAssertionForServer(<PublicKeyCredential>assertion);

        // post the assertion to the server for verification.
        try {
            const formData = new FormData();
            formData.set("response", JSON.stringify(<DeviceChallenge>{
                device_class: this.deviceChallenge?.device_class,
                device_uid: this.deviceChallenge?.device_uid,
                challenge: transformedAssertionForServer,
            }));
            await this.host?.submit(formData);
        } catch (err) {
            throw new Error(gettext(`Error when validating assertion on server: ${err}`));
        }
    }

    firstUpdated(): void {
        this.authenticateWrapper();
    }

    async authenticateWrapper(): Promise<void> {
        if (this.authenticateRunning) {
            return;
        }
        this.authenticateRunning = true;
        this.authenticate().catch((e) => {
            console.error(gettext(e));
            this.authenticateMessage = e.toString();
        }).finally(() => {
            this.authenticateRunning = false;
        });
    }

    render(): TemplateResult {
        return html`<div class="">
            ${this.authenticateRunning ?
                html`<div class="pf-c-empty-state__content">
                        <div class="pf-l-bullseye">
                            <div class="pf-l-bullseye__item">
                                <ak-spinner size="${SpinnerSize.XLarge}"></ak-spinner>
                            </div>
                        </div>
                    </div>`:
                html`
                <div class="pf-c-form__group pf-m-action">
                    <p class="pf-m-block">${this.authenticateMessage}</p>
                    <button class="pf-c-button pf-m-primary pf-m-block" @click=${() => {
                        this.authenticateWrapper();
                    }}>
                        ${gettext("Retry authentication")}
                    </button>
                </div>`}
        </div>`;
    }

}
