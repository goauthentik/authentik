import { gettext } from "django";
import { LitElement, html, customElement, property, TemplateResult, CSSResult, css } from "lit-element";
import { unsafeHTML } from "lit-html/directives/unsafe-html";
import { getCookie } from "../../utils";
import "../../elements/stages/identification/IdentificationStage";
import "../../elements/stages/password/PasswordStage";
import "../../elements/stages/consent/ConsentStage";
import "../../elements/stages/email/EmailStage";
import "../../elements/stages/autosubmit/AutosubmitStage";
import "../../elements/stages/prompt/PromptStage";
import "../../elements/stages/authenticator_totp/AuthenticatorTOTPStage";
import "../../elements/stages/authenticator_static/AuthenticatorStaticStage";
import "../../elements/stages/authenticator_webauthn/WebAuthnAuthenticatorRegisterStage";
import { ShellChallenge, Challenge, ChallengeTypes, Flow, RedirectChallenge } from "../../api/Flows";
import { DefaultClient } from "../../api/Client";
import { IdentificationChallenge } from "../../elements/stages/identification/IdentificationStage";
import { PasswordChallenge } from "../../elements/stages/password/PasswordStage";
import { ConsentChallenge } from "../../elements/stages/consent/ConsentStage";
import { EmailChallenge } from "../../elements/stages/email/EmailStage";
import { AutosubmitChallenge } from "../../elements/stages/autosubmit/AutosubmitStage";
import { PromptChallenge } from "../../elements/stages/prompt/PromptStage";
import { AuthenticatorTOTPChallenge } from "../../elements/stages/authenticator_totp/AuthenticatorTOTPStage";
import { AuthenticatorStaticChallenge } from "../../elements/stages/authenticator_static/AuthenticatorStaticStage";
import { WebAuthnAuthenticatorRegisterChallenge } from "../../elements/stages/authenticator_webauthn/WebAuthnAuthenticatorRegisterStage";
import { COMMON_STYLES } from "../../common/styles";
import { SpinnerSize } from "../../elements/Spinner";

@customElement("ak-flow-executor")
export class FlowExecutor extends LitElement {
    @property()
    flowSlug = "";

    @property({attribute: false})
    challenge?: Challenge;

    @property({type: Boolean})
    loading = false;

    static get styles(): CSSResult[] {
        return COMMON_STYLES.concat(css`
            .ak-loading {
                display: flex;
                height: 100%;
                width: 100%;
                justify-content: center;
                align-items: center;
                position: absolute;
                background-color: #0303039e;
            }
            .ak-hidden {
                display: none;
            }
            :host {
                position: relative;
            }
        `);
    }

    constructor() {
        super();
        this.addEventListener("ak-flow-submit", () => {
            this.submit();
        });
    }

    submit(formData?: FormData): Promise<void> {
        const csrftoken = getCookie("authentik_csrf");
        const request = new Request(DefaultClient.makeUrl(["flows", "executor", this.flowSlug]), {
            headers: {
                "X-CSRFToken": csrftoken,
            },
        });
        this.loading = true;
        return fetch(request, {
            method: "POST",
            mode: "same-origin",
            body: formData,
        })
            .then((response) => {
                return response.json();
            })
            .then((data) => {
                this.challenge = data;
            })
            .catch((e) => {
                this.errorMessage(e);
            })
            .finally(() => {
                this.loading = false;
            });
    }

    firstUpdated(): void {
        this.loading = true;
        Flow.executor(this.flowSlug).then((challenge) => {
            this.challenge = challenge;
        }).catch((e) => {
            // Catch JSON or Update errors
            this.errorMessage(e);
        }).finally(() => {
            this.loading = false;
        });
    }

    errorMessage(error: string): void {
        this.challenge = <ShellChallenge>{
            type: ChallengeTypes.shell,
            body: `<style>
                    .ak-exception {
                        font-family: monospace;
                        overflow-x: scroll;
                    }
                </style>
                <header class="pf-c-login__main-header">
                    <h1 class="pf-c-title pf-m-3xl">
                        ${gettext("Whoops!")}
                    </h1>
                </header>
                <div class="pf-c-login__main-body">
                    <h3>${gettext("Something went wrong! Please try again later.")}</h3>
                    <pre class="ak-exception">${error}</pre>
                </div>`
        };
    }

    renderLoading(): TemplateResult {
        return html`<div class="ak-loading">
            <ak-spinner size=${SpinnerSize.XLarge}></ak-spinner>
        </div>`;
    }

    renderChallenge(): TemplateResult {
        if (!this.challenge) {
            return html``;
        }
        switch (this.challenge.type) {
            case ChallengeTypes.redirect:
                console.debug(`authentik/flows: redirecting to ${(this.challenge as RedirectChallenge).to}`);
                window.location.assign((this.challenge as RedirectChallenge).to);
                break;
            case ChallengeTypes.shell:
                return html`${unsafeHTML((this.challenge as ShellChallenge).body)}`;
            case ChallengeTypes.native:
                switch (this.challenge.component) {
                    case "ak-stage-identification":
                        return html`<ak-stage-identification .host=${this} .challenge=${this.challenge as IdentificationChallenge}></ak-stage-identification>`;
                    case "ak-stage-password":
                        return html`<ak-stage-password .host=${this} .challenge=${this.challenge as PasswordChallenge}></ak-stage-password>`;
                    case "ak-stage-consent":
                        return html`<ak-stage-consent .host=${this} .challenge=${this.challenge as ConsentChallenge}></ak-stage-consent>`;
                    case "ak-stage-email":
                        return html`<ak-stage-email .host=${this} .challenge=${this.challenge as EmailChallenge}></ak-stage-email>`;
                    case "ak-stage-autosubmit":
                        return html`<ak-stage-autosubmit .host=${this} .challenge=${this.challenge as AutosubmitChallenge}></ak-stage-autosubmit>`;
                    case "ak-stage-prompt":
                        return html`<ak-stage-prompt .host=${this} .challenge=${this.challenge as PromptChallenge}></ak-stage-prompt>`;
                    case "ak-stage-authenticator-totp":
                        return html`<ak-stage-authenticator-totp .host=${this} .challenge=${this.challenge as AuthenticatorTOTPChallenge}></ak-stage-authenticator-totp>`;
                    case "ak-stage-authenticator-static":
                        return html`<ak-stage-authenticator-static .host=${this} .challenge=${this.challenge as AuthenticatorStaticChallenge}></ak-stage-authenticator-static>`;
                    case "ak-stage-authenticator-webauthn-register":
                        return html`<ak-stage-authenticator-webauthn-register .host=${this} .challenge=${this.challenge as WebAuthnAuthenticatorRegisterChallenge}></ak-stage-authenticator-webauthn-register>`;
                    default:
                        break;
                }
                break;
            default:
                console.debug(`authentik/flows: unexpected data type ${this.challenge.type}`);
                break;
        }
        return html``;
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return this.renderLoading();
        }
        return html`
            ${this.loading ? this.renderLoading() : html``}
            ${this.renderChallenge()}
        `;
    }
}
