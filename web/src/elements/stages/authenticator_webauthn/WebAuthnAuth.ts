import { gettext } from "django";
import { customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { SpinnerSize } from "../../Spinner";
import { getCredentialRequestOptionsFromServer, postAssertionToServer, transformAssertionForServer, transformCredentialRequestOptions } from "./utils";

@customElement("ak-stage-webauthn-auth")
export class WebAuthnAuth extends LitElement {

    @property({ type: Boolean })
    authenticateRunning = false;

    @property()
    authenticateMessage = "";

    async authenticate(): Promise<void> {
        // post the login data to the server to retrieve the PublicKeyCredentialRequestOptions
        let credentialRequestOptionsFromServer;
        try {
            credentialRequestOptionsFromServer = await getCredentialRequestOptionsFromServer();
        } catch (err) {
            throw new Error(gettext(`Error when getting request options from server: ${err}`));
        }

        // convert certain members of the PublicKeyCredentialRequestOptions into
        // byte arrays as expected by the spec.
        const transformedCredentialRequestOptions = transformCredentialRequestOptions(
            credentialRequestOptionsFromServer);

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
        const transformedAssertionForServer = transformAssertionForServer(assertion);

        // post the assertion to the server for verification.
        try {
            await postAssertionToServer(transformedAssertionForServer);
        } catch (err) {
            throw new Error(gettext(`Error when validating assertion on server: ${err}`));
        }

        this.finishStage();
    }

    finishStage(): void {
        // Mark this stage as done
        this.dispatchEvent(
            new CustomEvent("ak-flow-submit", {
                bubbles: true,
                composed: true,
            })
        );
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
