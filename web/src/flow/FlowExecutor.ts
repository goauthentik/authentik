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
import { Interface } from "@goauthentik/elements/Interface";
import "@goauthentik/elements/LoadingOverlay";
import "@goauthentik/elements/ak-locale-context";
import "@goauthentik/flow/sources/apple/AppleLoginInit";
import "@goauthentik/flow/sources/plex/PlexLoginInit";
import "@goauthentik/flow/stages/FlowErrorStage";
import "@goauthentik/flow/stages/RedirectStage";
import { StageHost, SubmitOptions } from "@goauthentik/flow/stages/base";

import { msg } from "@lit/localize";
import { CSSResult, PropertyValues, TemplateResult, css, html, nothing } from "lit";
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
    CapabilitiesEnum,
    ChallengeChoices,
    ChallengeTypes,
    ContextualFlowInfo,
    FlowChallengeResponseRequest,
    FlowErrorChallenge,
    FlowLayoutEnum,
    FlowsApi,
    ResponseError,
    ShellChallenge,
    UiThemeEnum,
} from "@goauthentik/api";

@customElement("ak-flow-executor")
export class FlowExecutor extends Interface implements StageHost {
    @property()
    flowSlug: string = window.location.pathname.split("/")[3];

    private _challenge?: ChallengeTypes;

    @property({ attribute: false })
    set challenge(value: ChallengeTypes | undefined) {
        this._challenge = value;
        if (value?.flowInfo?.title) {
            document.title = `${value.flowInfo?.title} - ${this.brand?.brandingTitle}`;
        } else {
            document.title = this.brand?.brandingTitle || TITLE_DEFAULT;
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

    @state()
    flowInfo?: ContextualFlowInfo;

    ws: WebsocketClient;

    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFDrawer, PFButton, PFTitle, PFList, PFBackgroundImage].concat(css`
            :host {
                --pf-c-login__main-body--PaddingBottom: var(--pf-global--spacer--2xl);
            }
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
            @media (min-height: 60rem) {
                .pf-c-login.stacked .pf-c-login__main {
                    margin-top: 13rem;
                }
            }
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
            .pf-c-brand {
                padding-top: calc(
                    var(--pf-c-login__main-footer-links--PaddingTop) +
                        var(--pf-c-login__main-footer-links--PaddingBottom) +
                        var(--pf-c-login__main-body--PaddingBottom)
                );
                max-height: 9rem;
            }
            .ak-brand {
                display: flex;
                justify-content: center;
            }
            .ak-brand img {
                padding: 0 2rem;
                max-height: inherit;
            }
        `);
    }

    constructor() {
        super();
        this.ws = new WebsocketClient();
        if (window.location.search.includes("inspector")) {
            this.inspectorOpen = true;
        }
        this.addEventListener(EVENT_FLOW_INSPECTOR_TOGGLE, () => {
            this.inspectorOpen = !this.inspectorOpen;
        });
    }

    async getTheme(): Promise<UiThemeEnum> {
        return globalAK()?.brand.uiTheme || UiThemeEnum.Automatic;
    }

    async submit(
        payload?: FlowChallengeResponseRequest,
        options?: SubmitOptions,
    ): Promise<boolean> {
        if (!payload) return Promise.reject();
        if (!this.challenge) return Promise.reject();
        // @ts-expect-error
        payload.component = this.challenge.component;
        if (!options?.invisible) {
            this.loading = true;
        }
        try {
            const challenge = await new FlowsApi(DEFAULT_CONFIG).flowsExecutorSolve({
                flowSlug: this.flowSlug,
                query: window.location.search.substring(1),
                flowChallengeResponseRequest: payload,
            });
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
            return !this.challenge.responseErrors;
        } catch (exc: unknown) {
            this.errorMessage(exc as Error | ResponseError);
            return false;
        } finally {
            this.loading = false;
        }
    }

    async firstUpdated(): Promise<void> {
        configureSentry();
        if (this.config?.capabilities.includes(CapabilitiesEnum.CanDebug)) {
            this.inspectorOpen = true;
        }
        this.loading = true;
        try {
            const challenge = await new FlowsApi(DEFAULT_CONFIG).flowsExecutorGet({
                flowSlug: this.flowSlug,
                query: window.location.search.substring(1),
            });
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
        } catch (exc: unknown) {
            // Catch JSON or Update errors
            this.errorMessage(exc as Error | ResponseError);
        } finally {
            this.loading = false;
        }
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

    setShadowStyles(value: ContextualFlowInfo) {
        if (!value) {
            return;
        }
        this.shadowRoot
            ?.querySelectorAll<HTMLDivElement>(".pf-c-background-image")
            .forEach((bg) => {
                bg.style.setProperty("--ak-flow-background", `url('${value?.background}')`);
            });
    }

    // DOM post-processing has to happen after the render.
    updated(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("flowInfo") && this.flowInfo !== undefined) {
            this.setShadowStyles(this.flowInfo);
        }
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
                return html`<ak-flow-source-plex
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-flow-source-plex>`;
            case "ak-source-oauth-apple":
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
        const logo = html`<div class="pf-c-login__main-header pf-c-brand ak-brand">
            <img src="${first(this.brand?.brandingLogo, "")}" alt="authentik Logo" />
        </div>`;
        if (!this.challenge) {
            return html`${logo}<ak-empty-state ?loading=${true} header=${msg("Loading")}>
                </ak-empty-state>`;
        }
        return html`
            ${this.loading ? html`<ak-loading-overlay></ak-loading-overlay>` : nothing} ${logo}
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
        const prefilledFlow = globalAK()?.flow?.layout || FlowLayoutEnum.Stacked;
        if (this.challenge) {
            return this.challenge?.flowInfo?.layout || prefilledFlow;
        }
        return prefilledFlow;
    }

    getLayoutClass(): string {
        const layout = this.getLayout();
        switch (layout) {
            case FlowLayoutEnum.ContentLeft:
                return "pf-c-login__container";
            case FlowLayoutEnum.ContentRight:
                return "pf-c-login__container content-right";
            case FlowLayoutEnum.Stacked:
            default:
                return "ak-login-container";
        }
    }

    render(): TemplateResult {
        return html` <ak-locale-context>
            <div class="pf-c-background-image"></div>
            <div class="pf-c-page__drawer">
                <div class="pf-c-drawer ${this.inspectorOpen ? "pf-m-expanded" : "pf-m-collapsed"}">
                    <div class="pf-c-drawer__main">
                        <div class="pf-c-drawer__content">
                            <div class="pf-c-drawer__body">
                                <div class="pf-c-login ${this.getLayout()}">
                                    <div class="${this.getLayoutClass()}">
                                        <div class="pf-c-login__main">
                                            ${this.renderChallengeWrapper()}
                                        </div>
                                        <footer class="pf-c-login__footer">
                                            <ul class="pf-c-list pf-m-inline">
                                                ${this.brand?.uiFooterLinks?.map((link) => {
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
                                                                  href="https://unsplash.com/@theforestbirds"
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
