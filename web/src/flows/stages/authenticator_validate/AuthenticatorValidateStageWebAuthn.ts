import { gettext } from "django";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import { SpinnerSize } from "../../../elements/Spinner";
import { transformAssertionForServer, transformCredentialRequestOptions } from "../authenticator_webauthn/utils";
import { BaseStage } from "../base";
import { AuthenticatorValidateStage, AuthenticatorValidateStageChallenge, DeviceChallenge } from "./AuthenticatorValidateStage";

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

    @property({type: Boolean})
    showBackButton = false;

    static get styles(): CSSResult[] {
        return [PFLogin, PFForm, PFFormControl, PFTitle, PFButton];
    }

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
            formData.set("webauthn", JSON.stringify(transformedAssertionForServer));
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
        return html`<div class="pf-c-login__main-body">
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
        </div>
        <footer class="pf-c-login__main-footer">
            <ul class="pf-c-login__main-footer-links">
                ${this.showBackButton ?
                    html`<li class="pf-c-login__main-footer-links-item">
                        <button class="pf-c-button pf-m-secondary pf-m-block" @click=${() => {
                            if (!this.host) return;
                            (this.host as AuthenticatorValidateStage).selectedDeviceChallenge = undefined;
                        }}>
                            ${gettext("Return to device picker")}
                        </button>
                    </li>`:
                    html``}
            </ul>
        </footer>`;
    }

}
