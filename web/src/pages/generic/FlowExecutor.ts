import { gettext } from "django";
import { LitElement, html, customElement, property, TemplateResult, CSSResult, css } from "lit-element";
import { unsafeHTML } from "lit-html/directives/unsafe-html";
import "../../elements/stages/authenticator_static/AuthenticatorStaticStage";
import "../../elements/stages/authenticator_totp/AuthenticatorTOTPStage";
import "../../elements/stages/authenticator_validate/AuthenticatorValidateStage";
import "../../elements/stages/authenticator_webauthn/WebAuthnAuthenticatorRegisterStage";
import "../../elements/stages/autosubmit/AutosubmitStage";
import "../../elements/stages/captcha/CaptchaStage";
import "../../elements/stages/consent/ConsentStage";
import "../../elements/stages/email/EmailStage";
import "../../elements/stages/identification/IdentificationStage";
import "../../elements/stages/password/PasswordStage";
import "../../elements/stages/prompt/PromptStage";
import { ShellChallenge, RedirectChallenge } from "../../api/Flows";
import { IdentificationChallenge } from "../../elements/stages/identification/IdentificationStage";
import { PasswordChallenge } from "../../elements/stages/password/PasswordStage";
import { ConsentChallenge } from "../../elements/stages/consent/ConsentStage";
import { EmailChallenge } from "../../elements/stages/email/EmailStage";
import { AutosubmitChallenge } from "../../elements/stages/autosubmit/AutosubmitStage";
import { PromptChallenge } from "../../elements/stages/prompt/PromptStage";
import { AuthenticatorTOTPChallenge } from "../../elements/stages/authenticator_totp/AuthenticatorTOTPStage";
import { AuthenticatorStaticChallenge } from "../../elements/stages/authenticator_static/AuthenticatorStaticStage";
import { AuthenticatorValidateStageChallenge } from "../../elements/stages/authenticator_validate/AuthenticatorValidateStage";
import { WebAuthnAuthenticatorRegisterChallenge } from "../../elements/stages/authenticator_webauthn/WebAuthnAuthenticatorRegisterStage";
import { CaptchaChallenge } from "../../elements/stages/captcha/CaptchaStage";
import { COMMON_STYLES } from "../../common/styles";
import { SpinnerSize } from "../../elements/Spinner";
import { StageHost } from "../../elements/stages/base";
import { Challenge, ChallengeTypeEnum, FlowsApi } from "../../api";
import { DEFAULT_CONFIG } from "../../api/Config";

@customElement("ak-flow-executor")
export class FlowExecutor extends LitElement implements StageHost {
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
        this.loading = true;
        return new FlowsApi(DEFAULT_CONFIG).flowsExecutorSolve({
            flowSlug: this.flowSlug,
            data: formData || {},
        }).then((data) => {
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
        new FlowsApi(DEFAULT_CONFIG).flowsExecutorGet({
            flowSlug: this.flowSlug
        }).then((challenge) => {
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
            type: ChallengeTypeEnum.Shell,
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
            case ChallengeTypeEnum.Redirect:
                console.debug(`authentik/flows: redirecting to ${(this.challenge as RedirectChallenge).to}`);
                window.location.assign((this.challenge as RedirectChallenge).to);
                break;
            case ChallengeTypeEnum.Shell:
                return html`${unsafeHTML((this.challenge as ShellChallenge).body)}`;
            case ChallengeTypeEnum.Native:
                switch (this.challenge.component) {
                    case "ak-stage-identification":
                        return html`<ak-stage-identification .host=${this} .challenge=${this.challenge as IdentificationChallenge}></ak-stage-identification>`;
                    case "ak-stage-password":
                        return html`<ak-stage-password .host=${this} .challenge=${this.challenge as PasswordChallenge}></ak-stage-password>`;
                    case "ak-stage-captcha":
                        return html`<ak-stage-captcha .host=${this} .challenge=${this.challenge as CaptchaChallenge}></ak-stage-captcha>`;
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
                    case "ak-stage-authenticator-webauthn":
                        return html`<ak-stage-authenticator-webauthn .host=${this} .challenge=${this.challenge as WebAuthnAuthenticatorRegisterChallenge}></ak-stage-authenticator-webauthn>`;
                    case "ak-stage-authenticator-validate":
                        return html`<ak-stage-authenticator-validate .host=${this} .challenge=${this.challenge as AuthenticatorValidateStageChallenge}></ak-stage-authenticator-validate>`;
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
