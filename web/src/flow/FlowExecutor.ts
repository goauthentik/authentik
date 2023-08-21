import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import {
    EVENT_FLOW_ADVANCE,
    EVENT_FLOW_INSPECTOR_TOGGLE,
    TITLE_DEFAULT,
} from "@goauthentik/common/constants";
import { globalAK } from "@goauthentik/common/global";
import { configureSentry } from "@goauthentik/common/sentry";
import { first } from "@goauthentik/common/utils";
import { WebsocketClient } from "@goauthentik/common/ws";
import { Interface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/LoadingOverlay";
import "@goauthentik/elements/ak-locale-context";
import "@goauthentik/flow/stages/FlowErrorStage";
import "@goauthentik/flow/stages/RedirectStage";
import { StageHost } from "@goauthentik/flow/stages/base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html, render } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";
import { until } from "lit/directives/until.js";

import PFBackgroundImage from "@patternfly/patternfly/components/BackgroundImage/background-image.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    ChallengeChoices,
    ChallengeTypes,
    ContextualFlowInfo,
    FlowChallengeResponseRequest,
    FlowErrorChallenge,
    FlowsApi,
    LayoutEnum,
    ResponseError,
    ShellChallenge,
    UiThemeEnum,
} from "@goauthentik/api";

@customElement("ak-flow-executor")
export class FlowExecutor extends Interface implements StageHost {
    flowSlug?: string;

    private _challenge?: ChallengeTypes;

    @property({ attribute: false })
    set challenge(value: ChallengeTypes | undefined) {
        this._challenge = value;
        if (value?.flowInfo?.title) {
            document.title = `${value.flowInfo?.title} - ${this.tenant?.brandingTitle}`;
        } else {
            document.title = this.tenant?.brandingTitle || TITLE_DEFAULT;
        }
        this.requestUpdate();
    }

    get challenge(): ChallengeTypes | undefined {
        return this._challenge;
    }

    @property({ type: Boolean })
    loading = false;

    @state()
    inspectorOpen = false;

    _flowInfo?: ContextualFlowInfo;

    @state()
    set flowInfo(value: ContextualFlowInfo | undefined) {
        this._flowInfo = value;
        if (!value) {
            return;
        }
        this.shadowRoot
            ?.querySelectorAll<HTMLDivElement>(".pf-c-background-image")
            .forEach((bg) => {
                bg.style.setProperty("--ak-flow-background", `url('${value?.background}')`);
            });
    }

    get flowInfo(): ContextualFlowInfo | undefined {
        return this._flowInfo;
    }

    ws: WebsocketClient;

    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFDrawer, PFButton, PFTitle, PFList, PFBackgroundImage].concat(css`
            .pf-c-background-image::before {
                --pf-c-background-image--BackgroundImage: var(--ak-flow-background);
                --pf-c-background-image--BackgroundImage-2x: var(--ak-flow-background);
                --pf-c-background-image--BackgroundImage--sm: var(--ak-flow-background);
                --pf-c-background-image--BackgroundImage--sm-2x: var(--ak-flow-background);
                --pf-c-background-image--BackgroundImage--lg: var(--ak-flow-background);
            }
            .ak-hidden {
                display: none;
            }
            :host {
                position: relative;
            }
            .pf-c-drawer__content {
                background-color: transparent;
            }
            /* layouts */
            .pf-c-login__container.content-right {
                grid-template-areas:
                    "header main"
                    "footer main"
                    ". main";
            }
            .pf-c-login.sidebar_left {
                justify-content: flex-start;
                padding-top: 0;
                padding-bottom: 0;
            }
            .pf-c-login.sidebar_left .ak-login-container,
            .pf-c-login.sidebar_right .ak-login-container {
                height: 100vh;
                background-color: var(--pf-c-login__main--BackgroundColor);
                padding-left: var(--pf-global--spacer--lg);
                padding-right: var(--pf-global--spacer--lg);
            }
            .pf-c-login.sidebar_left .pf-c-list,
            .pf-c-login.sidebar_right .pf-c-list {
                color: #000;
            }
            .pf-c-login.sidebar_right {
                justify-content: flex-end;
                padding-top: 0;
                padding-bottom: 0;
            }
            :host([theme="dark"]) .pf-c-login.sidebar_left .ak-login-container,
            :host([theme="dark"]) .pf-c-login.sidebar_right .ak-login-container {
                background-color: var(--ak-dark-background);
            }
            :host([theme="dark"]) .pf-c-login.sidebar_left .pf-c-list,
            :host([theme="dark"]) .pf-c-login.sidebar_right .pf-c-list {
                color: var(--ak-dark-foreground);
            }
        `);
    }

    constructor() {
        super();
        this.ws = new WebsocketClient();
        this.flowSlug = window.location.pathname.split("/")[3];
        if (window.location.search.includes("inspector")) {
            this.inspectorOpen = !this.inspectorOpen;
        }
        this.addEventListener(EVENT_FLOW_INSPECTOR_TOGGLE, () => {
            this.inspectorOpen = !this.inspectorOpen;
        });
    }

    async getTheme(): Promise<UiThemeEnum> {
        return globalAK()?.tenant.uiTheme || UiThemeEnum.Automatic;
    }

    submit(payload?: FlowChallengeResponseRequest): Promise<boolean> {
        if (!payload) return Promise.reject();
        if (!this.challenge) return Promise.reject();
        // @ts-ignore
        payload.component = this.challenge.component;
        this.loading = true;
        return new FlowsApi(DEFAULT_CONFIG)
            .flowsExecutorSolve({
                flowSlug: this.flowSlug || "",
                query: window.location.search.substring(1),
                flowChallengeResponseRequest: payload,
            })
            .then((data) => {
                if (this.inspectorOpen) {
                    window.dispatchEvent(
                        new CustomEvent(EVENT_FLOW_ADVANCE, {
                            bubbles: true,
                            composed: true,
                        }),
                    );
                }
                this.challenge = data;
                if (this.challenge.flowInfo) {
                    this.flowInfo = this.challenge.flowInfo;
                }
                if (this.challenge.responseErrors) {
                    return false;
                }
                return true;
            })
            .catch((e: Error | ResponseError) => {
                this.errorMessage(e);
                return false;
            })
            .finally(() => {
                this.loading = false;
                return false;
            });
    }

    firstUpdated(): void {
        configureSentry();
        this.loading = true;
        new FlowsApi(DEFAULT_CONFIG)
            .flowsExecutorGet({
                flowSlug: this.flowSlug || "",
                query: window.location.search.substring(1),
            })
            .then((challenge) => {
                if (this.inspectorOpen) {
                    window.dispatchEvent(
                        new CustomEvent(EVENT_FLOW_ADVANCE, {
                            bubbles: true,
                            composed: true,
                        }),
                    );
                }
                this.challenge = challenge;
                if (this.challenge.flowInfo) {
                    this.flowInfo = this.challenge.flowInfo;
                }
            })
            .catch((e: Error | ResponseError) => {
                // Catch JSON or Update errors
                this.errorMessage(e);
            })
            .finally(() => {
                this.loading = false;
            });
    }

    async errorMessage(error: Error | ResponseError): Promise<void> {
        let body = "";
        if (error instanceof ResponseError) {
            body = await error.response.text();
        } else if (error instanceof Error) {
            body = error.message;
        }
        const challenge: FlowErrorChallenge = {
            type: ChallengeChoices.Native,
            component: "ak-stage-flow-error",
            error: body,
            requestId: "",
        };
        this.challenge = challenge as ChallengeTypes;
    }

    async renderChallengeNativeElement(): Promise<TemplateResult> {
        switch (this.challenge?.component) {
            case "ak-stage-access-denied":
                await import("@goauthentik/flow/stages/access_denied/AccessDeniedStage");
                return html`<ak-stage-access-denied
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-stage-access-denied>`;
            case "ak-stage-identification":
                await import("@goauthentik/flow/stages/identification/IdentificationStage");
                return html`<ak-stage-identification
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-stage-identification>`;
            case "ak-stage-password":
                await import("@goauthentik/flow/stages/password/PasswordStage");
                return html`<ak-stage-password
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-stage-password>`;
            case "ak-stage-captcha":
                await import("@goauthentik/flow/stages/captcha/CaptchaStage");
                return html`<ak-stage-captcha
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-stage-captcha>`;
            case "ak-stage-consent":
                await import("@goauthentik/flow/stages/consent/ConsentStage");
                return html`<ak-stage-consent
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-stage-consent>`;
            case "ak-stage-dummy":
                await import("@goauthentik/flow/stages/dummy/DummyStage");
                return html`<ak-stage-dummy
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-stage-dummy>`;
            case "ak-stage-email":
                await import("@goauthentik/flow/stages/email/EmailStage");
                return html`<ak-stage-email
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-stage-email>`;
            case "ak-stage-autosubmit":
                await import("@goauthentik/flow/stages/autosubmit/AutosubmitStage");
                return html`<ak-stage-autosubmit
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-stage-autosubmit>`;
            case "ak-stage-prompt":
                await import("@goauthentik/flow/stages/prompt/PromptStage");
                return html`<ak-stage-prompt
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-stage-prompt>`;
            case "ak-stage-authenticator-totp":
                await import("@goauthentik/flow/stages/authenticator_totp/AuthenticatorTOTPStage");
                return html`<ak-stage-authenticator-totp
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-stage-authenticator-totp>`;
            case "ak-stage-authenticator-duo":
                await import("@goauthentik/flow/stages/authenticator_duo/AuthenticatorDuoStage");
                return html`<ak-stage-authenticator-duo
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-stage-authenticator-duo>`;
            case "ak-stage-authenticator-static":
                await import(
                    "@goauthentik/flow/stages/authenticator_static/AuthenticatorStaticStage"
                );
                return html`<ak-stage-authenticator-static
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-stage-authenticator-static>`;
            case "ak-stage-authenticator-webauthn":
                return html`<ak-stage-authenticator-webauthn
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-stage-authenticator-webauthn>`;
            case "ak-stage-authenticator-sms":
                await import("@goauthentik/flow/stages/authenticator_sms/AuthenticatorSMSStage");
                return html`<ak-stage-authenticator-sms
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-stage-authenticator-sms>`;
            case "ak-stage-authenticator-validate":
                await import(
                    "@goauthentik/flow/stages/authenticator_validate/AuthenticatorValidateStage"
                );
                return html`<ak-stage-authenticator-validate
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-stage-authenticator-validate>`;
            case "ak-stage-user-login":
                await import("@goauthentik/flow/stages/user_login/UserLoginStage");
                return html`<ak-stage-user-login
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-stage-user-login>`;
            // Sources
            case "ak-source-plex":
                await import("@goauthentik/flow/sources/plex/PlexLoginInit");
                return html`<ak-flow-source-plex
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-flow-source-plex>`;
            case "ak-source-oauth-apple":
                await import("@goauthentik/flow/sources/apple/AppleLoginInit");
                return html`<ak-flow-source-oauth-apple
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-flow-source-oauth-apple>`;
            // Providers
            case "ak-provider-oauth2-device-code":
                await import("@goauthentik/flow/providers/oauth2/DeviceCode");
                return html`<ak-flow-provider-oauth2-code
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-flow-provider-oauth2-code>`;
            case "ak-provider-oauth2-device-code-finish":
                await import("@goauthentik/flow/providers/oauth2/DeviceCodeFinish");
                return html`<ak-flow-provider-oauth2-code-finish
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-flow-provider-oauth2-code-finish>`;
            // Internal stages
            case "ak-stage-flow-error":
                return html`<ak-stage-flow-error
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-stage-flow-error>`;
            default:
                return html`Invalid native challenge element`;
        }
    }

    async renderChallenge(): Promise<TemplateResult> {
        if (!this.challenge) {
            return html``;
        }
        switch (this.challenge.type) {
            case ChallengeChoices.Redirect:
                return html`<ak-stage-redirect
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                    ?promptUser=${this.inspectorOpen}
                >
                </ak-stage-redirect>`;
            case ChallengeChoices.Shell:
                return html`${unsafeHTML((this.challenge as ShellChallenge).body)}`;
            case ChallengeChoices.Native:
                return await this.renderChallengeNativeElement();
            default:
                console.debug(`authentik/flows: unexpected data type ${this.challenge.type}`);
                break;
        }
        return html``;
    }

    renderChallengeWrapper(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state ?loading=${true} header=${msg("Loading")}>
            </ak-empty-state>`;
        }
        return html`
            ${this.loading ? html`<ak-loading-overlay></ak-loading-overlay>` : html``}
            ${until(this.renderChallenge())}
        `;
    }

    async renderInspector(): Promise<TemplateResult> {
        if (!this.inspectorOpen) {
            return html``;
        }
        await import("@goauthentik/flow/FlowInspector");
        return html`<ak-flow-inspector
            class="pf-c-drawer__panel pf-m-width-33"
        ></ak-flow-inspector>`;
    }

    getLayout(): string {
        const prefilledFlow = globalAK()?.flow?.layout || LayoutEnum.Stacked;
        if (this.challenge) {
            return this.challenge?.flowInfo?.layout || prefilledFlow;
        }
        return prefilledFlow;
    }

    getLayoutClass(): string {
        const layout = this.getLayout();
        switch (layout) {
            case LayoutEnum.ContentLeft:
                return "pf-c-login__container";
            case LayoutEnum.ContentRight:
                return "pf-c-login__container content-right";
            case LayoutEnum.Stacked:
            default:
                return "ak-login-container";
        }
    }

    renderBackgroundOverlay(): TemplateResult {
        const overlaySVG = html`<svg
            xmlns="http://www.w3.org/2000/svg"
            class="pf-c-background-image__filter"
            width="0"
            height="0"
        >
            <filter id="image_overlay">
                <feColorMatrix
                    in="SourceGraphic"
                    type="matrix"
                    values="1.3 0 0 0 0 0 1.3 0 0 0 0 0 1.3 0 0 0 0 0 1 0"
                />
                <feComponentTransfer color-interpolation-filters="sRGB" result="duotone">
                    <feFuncR
                        type="table"
                        tableValues="0.086274509803922 0.43921568627451"
                    ></feFuncR>
                    <feFuncG
                        type="table"
                        tableValues="0.086274509803922 0.43921568627451"
                    ></feFuncG>
                    <feFuncB
                        type="table"
                        tableValues="0.086274509803922 0.43921568627451"
                    ></feFuncB>
                    <feFuncA type="table" tableValues="0 1"></feFuncA>
                </feComponentTransfer>
            </filter>
        </svg>`;
        render(overlaySVG, document.body);
        return overlaySVG;
    }

    render(): TemplateResult {
        return html` <ak-locale-context>
            <div class="pf-c-background-image">${this.renderBackgroundOverlay()}</div>
            <div class="pf-c-page__drawer">
                <div class="pf-c-drawer ${this.inspectorOpen ? "pf-m-expanded" : "pf-m-collapsed"}">
                    <div class="pf-c-drawer__main">
                        <div class="pf-c-drawer__content">
                            <div class="pf-c-drawer__body">
                                <div class="pf-c-login ${this.getLayout()}">
                                    <div class="${this.getLayoutClass()}">
                                        <header class="pf-c-login__header">
                                            <div class="pf-c-brand ak-brand">
                                                <img
                                                    src="${first(this.tenant?.brandingLogo, "")}"
                                                    alt="authentik Logo"
                                                />
                                            </div>
                                        </header>
                                        <div class="pf-c-login__main">
                                            ${this.renderChallengeWrapper()}
                                        </div>
                                        <footer class="pf-c-login__footer">
                                            <p></p>
                                            <ul class="pf-c-list pf-m-inline">
                                                ${this.tenant?.uiFooterLinks?.map((link) => {
                                                    return html`<li>
                                                        <a href="${link.href || ""}"
                                                            >${link.name}</a
                                                        >
                                                    </li>`;
                                                })}
                                                <li>
                                                    <a
                                                        href="https://goauthentik.io?utm_source=authentik&amp;utm_medium=flow"
                                                        >${msg("Powered by authentik")}</a
                                                    >
                                                </li>
                                                ${this.flowInfo?.background?.startsWith("/static")
                                                    ? html`
                                                          <li>
                                                              <a
                                                                  href="https://unsplash.com/@sgabriel"
                                                                  >${msg("Background image")}</a
                                                              >
                                                          </li>
                                                      `
                                                    : html``}
                                            </ul>
                                        </footer>
                                    </div>
                                </div>
                            </div>
                        </div>
                        ${until(this.renderInspector())}
                    </div>
                </div>
            </div>
        </ak-locale-context>`;
    }
}
