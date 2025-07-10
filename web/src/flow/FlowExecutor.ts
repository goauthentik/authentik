import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_FLOW_ADVANCE, EVENT_FLOW_INSPECTOR_TOGGLE } from "#common/constants";
import { globalAK } from "#common/global";
import { configureSentry } from "#common/sentry/index";
import { WebsocketClient } from "#common/ws";
import { Interface } from "#elements/Interface";
import "#elements/LoadingOverlay";
import "#elements/ak-locale-context/ak-locale-context";
import { WithBrandConfig } from "#elements/mixins/branding";
import { WithCapabilitiesConfig } from "#elements/mixins/capabilities";
import { themeImage } from "#elements/utils/images";
import "#flow/components/ak-brand-footer";
import "#flow/components/ak-flow-card";
import "#flow/sources/apple/AppleLoginInit";
import "#flow/sources/plex/PlexLoginInit";
import "#flow/stages/FlowErrorStage";
import "#flow/stages/FlowFrameStage";
import "#flow/stages/RedirectStage";
import { BaseStage, StageHost, SubmitOptions } from "#flow/stages/base";

import { msg } from "@lit/localize";
import {
    CSSResult,
    MaybeCompiledTemplateResult,
    PropertyValues,
    TemplateResult,
    css,
    html,
    nothing,
} from "lit";
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
    ChallengeTypes,
    ContextualFlowInfo,
    FetchError,
    FlowChallengeResponseRequest,
    FlowErrorChallenge,
    FlowLayoutEnum,
    FlowsApi,
    ResponseError,
    ShellChallenge,
} from "@goauthentik/api";

@customElement("ak-flow-executor")
export class FlowExecutor
    extends WithCapabilitiesConfig(WithBrandConfig(Interface))
    implements StageHost
{
    @property()
    flowSlug: string = window.location.pathname.split("/")[3];

    private _challenge?: ChallengeTypes;

    @property({ attribute: false })
    set challenge(value: ChallengeTypes | undefined) {
        this._challenge = value;
        if (value?.flowInfo?.title) {
            document.title = `${value.flowInfo?.title} - ${this.brandingTitle}`;
        } else {
            document.title = this.brandingTitle;
        }
        if (value?.flowInfo) {
            this.flowInfo = value.flowInfo;
        } else {
            this.requestUpdate();
        }
    }

    get challenge(): ChallengeTypes | undefined {
        return this._challenge;
    }

    @property({ type: Boolean })
    loading = false;

    @state()
    inspectorOpen = false;

    @state()
    inspectorAvailable = false;

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
            .inspector-toggle {
                position: absolute;
                top: 1rem;
                right: 1rem;
                z-index: 100;
            }
        `);
    }

    constructor() {
        configureSentry();
        super();
        this.ws = new WebsocketClient();
        const inspector = new URL(window.location.toString()).searchParams.get("inspector");
        if (inspector === "" || inspector === "open") {
            this.inspectorOpen = true;
            this.inspectorAvailable = true;
        } else if (inspector === "available") {
            this.inspectorAvailable = true;
        }
        this.addEventListener(EVENT_FLOW_INSPECTOR_TOGGLE, () => {
            this.inspectorOpen = !this.inspectorOpen;
        });
        window.addEventListener("message", (event) => {
            const msg: {
                source?: string;
                context?: string;
                message: string;
            } = event.data;
            if (msg.source !== "goauthentik.io" || msg.context !== "flow-executor") {
                return;
            }
            if (msg.message === "submit") {
                this.submit({} as FlowChallengeResponseRequest);
            }
        });
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
            return !this.challenge.responseErrors;
        } catch (exc: unknown) {
            this.errorMessage(exc as Error | ResponseError | FetchError);
            return false;
        } finally {
            this.loading = false;
        }
    }

    async firstUpdated(): Promise<void> {
        if (this.can(CapabilitiesEnum.CanDebug)) {
            this.inspectorAvailable = true;
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
        } catch (exc: unknown) {
            // Catch JSON or Update errors
            this.errorMessage(exc as Error | ResponseError | FetchError);
        } finally {
            this.loading = false;
        }
    }

    async errorMessage(error: Error | ResponseError | FetchError): Promise<void> {
        let body = "";
        if (error instanceof FetchError) {
            body = msg("Request failed. Please try again later.");
        } else if (error instanceof ResponseError) {
            body = await error.response.text();
        } else if (error instanceof Error) {
            body = error.message;
        }
        const challenge: FlowErrorChallenge = {
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

    //#region Render Challenge

    async #registerChallengeComponent(component: ChallengeTypes["component"]) {
        switch (component) {
            //#region Stages

            case "ak-stage-access-denied":
                return import("#flow/stages/access_denied/AccessDeniedStage");
            case "ak-stage-identification":
                return import("#flow/stages/identification/IdentificationStage");
            case "ak-stage-password":
                return import("#flow/stages/password/PasswordStage");
            case "ak-stage-captcha":
                return import("#flow/stages/captcha/CaptchaStage");
            case "ak-stage-consent":
                return import("#flow/stages/consent/ConsentStage");
            case "ak-stage-dummy":
                return import("#flow/stages/dummy/DummyStage");
            case "ak-stage-email":
                return import("#flow/stages/email/EmailStage");
            case "ak-stage-autosubmit":
                return import("#flow/stages/autosubmit/AutosubmitStage");
            case "ak-stage-prompt":
                return import("#flow/stages/prompt/PromptStage");
            case "ak-stage-authenticator-totp":
                return import("#flow/stages/authenticator_totp/AuthenticatorTOTPStage");
            case "ak-stage-authenticator-duo":
                return import("#flow/stages/authenticator_duo/AuthenticatorDuoStage");
            case "ak-stage-authenticator-static":
                return import("#flow/stages/authenticator_static/AuthenticatorStaticStage");
            case "ak-stage-authenticator-email":
                return import("#flow/stages/authenticator_email/AuthenticatorEmailStage");
            case "ak-stage-authenticator-sms":
                return import("#flow/stages/authenticator_sms/AuthenticatorSMSStage");
            case "ak-stage-authenticator-validate":
                return import("#flow/stages/authenticator_validate/AuthenticatorValidateStage");
            case "ak-stage-user-login":
                return import("#flow/stages/user_login/UserLoginStage");
            case "ak-stage-session-end":
                return import("#flow/providers/SessionEnd");

            //#endregion

            //#region Providers

            case "ak-provider-oauth2-device-code":
                return import("#flow/providers/oauth2/DeviceCode");
            case "ak-provider-oauth2-device-code-finish":
                return import("#flow/providers/oauth2/DeviceCodeFinish");

            //#endregion
        }
    }

    async renderChallenge(): Promise<MaybeCompiledTemplateResult | HTMLElement> {
        const { challenge } = this;

        if (!challenge) {
            return html`<ak-flow-card loading></ak-flow-card>`;
        }

        const { component } = challenge;

        await this.#registerChallengeComponent(component);

        switch (component) {
            case "xak-flow-redirect":
                return html`<ak-stage-redirect
                    .host=${this}
                    .challenge=${challenge}
                    ?promptUser=${this.inspectorOpen}
                >
                </ak-stage-redirect>`;
            case "xak-flow-frame":
                return html`<xak-flow-frame
                    .host=${this}
                    .challenge=${challenge}
                ></xak-flow-frame>`;
            case "xak-flow-shell":
                return html`${unsafeHTML((challenge as ShellChallenge).body)}`;
        }

        const ElementConstructor = customElements.get(component);

        if (!ElementConstructor) {
            return html`Invalid native challenge element "${component}"`;
        }

        const element = document.createElement(component) as BaseStage<ChallengeTypes, unknown>;

        element.host = this;
        element.challenge = this.challenge!;

        return element;
    }

    //#endregion

    async renderInspector() {
        if (!this.inspectorOpen) {
            return nothing;
        }
        await import("@goauthentik/flow/FlowInspector");
        return html`<ak-flow-inspector
            class="pf-c-drawer__panel pf-m-width-33"
            .flowSlug=${this.flowSlug}
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
                                            ${this.loading && this.challenge
                                                ? html`<ak-loading-overlay></ak-loading-overlay>`
                                                : nothing}
                                            <div
                                                class="pf-c-login__main-header pf-c-brand ak-brand"
                                            >
                                                <img
                                                    src="${themeImage(this.brandingLogo)}"
                                                    alt="${msg("authentik Logo")}"
                                                />
                                            </div>
                                            ${until(this.renderChallenge())}
                                        </div>
                                        <ak-brand-links
                                            class="pf-c-login__footer"
                                            .links=${this.brandingFooterLinks}
                                        ></ak-brand-links>
                                    </div>
                                </div>
                            </div>
                        </div>
                        ${(this.inspectorAvailable ?? !this.inspectorOpen)
                            ? html`<button
                                  class="inspector-toggle pf-c-button pf-m-primary"
                                  @click=${() => {
                                      this.inspectorOpen = true;
                                  }}
                              >
                                  <i class="fa fa-search-plus" aria-hidden="true"></i>
                              </button>`
                            : nothing}
                        ${until(this.renderInspector())}
                    </div>
                </div>
            </div>
        </ak-locale-context>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-executor": FlowExecutor;
    }
}
